from datetime import date, datetime
from typing import List, Literal, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..database import get_supabase
from ..progression import parse_target_reps, should_progress, next_weight, suggest_next_set, set_type_guidance
from ..math_engine import warmup_sets, epley_e1rm, plate_breakdown, effective_weight, compare_exercise_to_last

router = APIRouter(prefix="/api/workouts", tags=["workouts"])
legacy_router = APIRouter(prefix="/api", tags=["legacy"])

class SetLog(BaseModel):
    exercise_id: str
    set_number: int
    set_type: Literal["normal","drop_set","rest_pause","pyramid"] = "normal"
    weight: float
    reps: int
    rir: int

class CompleteRequest(BaseModel):
    user_id: str
    plan_id: Optional[str] = None
    day_number: Optional[int] = None
    sets: List[SetLog]

class CardioCompleteRequest(BaseModel):
    user_id: str
    plan_id: Optional[str] = None
    total_duration_minutes: int = 45
    emom_rounds_completed: int = 3
    perceived_effort_rpe: int = 8
    notes: Optional[str] = ""

class SuggestRequest(BaseModel):
    exercise_id: str
    plan_id: Optional[str] = None
    weight: float
    reps: int
    rir: int
    target_reps: Optional[str] = None
    mechanics: Optional[str] = "compound"
    cns_load: Optional[int] = 3
    target_muscle: Optional[str] = ""
    set_type: Optional[str] = "normal"

class LegacySetLog(BaseModel):
    exercise_id: str
    set_number: int
    weight: float
    reps: int
    rir: int

class LegacyFinishRequest(BaseModel):
    user_id: str
    day_number: int
    sets: List[LegacySetLog]

def fetch_plan_exercise_meta(sb, plan_id, exercise_id):
    try:
        r = sb.table("plan_exercises").select("target_reps, exercises(mechanics, cns_load, target_muscle, is_assisted)").eq("plan_id", plan_id).eq("exercise_id", exercise_id).limit(1).execute()
        if r.data:
            row = r.data[0]
            ex = row.get("exercises") or {}
            return row["target_reps"], ex.get("mechanics", "compound"), ex.get("cns_load", 3), ex.get("target_muscle", ""), bool(ex.get("is_assisted", False))
    except Exception:
        pass
    return None

def _meta_tuple(meta):
    """Совместимость: meta может быть (tr,mech,cns,mus) или (tr,mech,cns,mus,assisted)."""
    if not meta:
        return None
    if len(meta) == 5:
        return meta
    tr, mech, cns, mus = meta
    return (tr, mech, cns, mus, False)

@router.post("/suggest-next-set")
async def suggest_next_set_endpoint(req: SuggestRequest):
    # if target_reps not provided, fetch from DB
    tr = req.target_reps
    mech = req.mechanics
    cns = req.cns_load
    mus = req.target_muscle
    if not tr and req.plan_id:
        try:
            sb = get_supabase()
            meta = _meta_tuple(fetch_plan_exercise_meta(sb, req.plan_id, req.exercise_id))
            if meta:
                tr, mech, cns, mus, _assist = meta
        except Exception:
            pass
    tr = tr or "8-12"
    suggestion = suggest_next_set(req.rir, req.reps, tr, req.weight, mech, cns, mus)
    warmup = warmup_sets(suggestion["next_weight"] if suggestion["action"]=="increase" else req.weight)
    plates = plate_breakdown(suggestion["next_weight"])
    guidance = set_type_guidance(req.set_type, req.weight)
    return {**suggestion, "warmup": warmup, "plates": plates, "target_reps": tr, "method": guidance}

@router.post("/complete")
async def complete_workout(req: CompleteRequest):
    sb = get_supabase()
    try:
        # Вес тела нужен для инвертированной математики гравитрона
        bodyweight = 0.0
        try:
            u = sb.table("users").select("current_weight").eq("id", req.user_id).limit(1).execute()
            if u.data and u.data[0].get("current_weight"):
                bodyweight = float(u.data[0]["current_weight"])
        except Exception:
            pass
        log_id = None
        try:
            payload = {"user_id": req.user_id, "plan_id": req.plan_id, "date": str(date.today()),
                       "day_number": req.day_number, "completed": True}
            ins = sb.table("workout_logs").insert(payload).execute()
            log_id = ins.data[0]["id"] if ins.data else None
        except Exception:
            try:
                ins = sb.table("workout_logs").insert({"user_id": req.user_id, "plan_id": req.plan_id, "date": str(date.today()), "completed": True}).execute()
                log_id = ins.data[0]["id"] if ins.data else None
            except Exception:
                log_id = None
        progressions=[]
        logged=0
        last_per_ex={}
        best_per_ex={}
        for s in req.sets:
            last_per_ex[s.exercise_id]=s
            prev = best_per_ex.get(s.exercise_id)
            sw = float(s.weight or 0)
            sr = int(s.reps or 0)
            if prev is None or (sr > int(prev.get("reps") or 0)) or (sr == int(prev.get("reps") or 0) and sw > float(prev.get("weight") or 0)):
                best_per_ex[s.exercise_id] = {"weight": sw, "reps": sr}
        # Карта is_assisted для упражнений сессии
        assist_map = {}
        try:
            ids = list(last_per_ex.keys())
            for i in range(0, len(ids), 20):
                chunk = ids[i:i+20]
                r = sb.table("exercises").select("id,is_assisted").in_("id", chunk).execute()
                for row in (r.data or []):
                    assist_map[row["id"]] = bool(row.get("is_assisted", False))
        except Exception:
            pass
        # Предыдущие лучшие сеты по упражнениям (последний лог до текущего)
        prev_best_map = {}
        prev_session_tonnage = None
        try:
            logs = sb.table("workout_logs").select("id,date").eq("user_id", req.user_id).eq("completed", True).order("date", desc=True).limit(12).execute().data or []
            logs = [l for l in logs if l["id"] != log_id]
            if logs:
                first = logs[0]
                try:
                    psets = sb.table("workout_sets").select("exercise_id,weight,reps").eq("log_id", first["id"]).execute().data or []
                    t = 0.0
                    for ps in psets:
                        try:
                            t += float(ps.get("weight") or 0) * int(ps.get("reps") or 0)
                        except (TypeError, ValueError):
                            pass
                    prev_session_tonnage = round(t, 1)
                except Exception:
                    pass
                for l in logs:
                    try:
                        psets = sb.table("workout_sets").select("exercise_id,weight,reps").eq("log_id", l["id"]).execute().data or []
                    except Exception:
                        continue
                    for ps in psets:
                        eid = ps.get("exercise_id")
                        if eid in last_per_ex and eid not in prev_best_map:
                            try:
                                prev_best_map[eid] = {"weight": float(ps.get("weight") or 0), "reps": int(ps.get("reps") or 0)}
                            except (TypeError, ValueError):
                                pass
                    if len(prev_best_map) >= len(last_per_ex):
                        break
        except Exception:
            pass
        for s in req.sets:
            if log_id:
                try:
                    sb.table("workout_sets").insert({"log_id": log_id, "exercise_id": s.exercise_id, "set_number": s.set_number, "set_type": s.set_type, "weight": s.weight, "reps": s.reps, "rir": s.rir}).execute()
                except Exception:
                    sb.table("workout_logs").insert({"user_id": req.user_id, "exercise_id": s.exercise_id, "weight": s.weight, "reps": s.reps, "rir": s.rir, "date": datetime.utcnow().isoformat()}).execute()
            else:
                sb.table("workout_logs").insert({"user_id": req.user_id, "exercise_id": s.exercise_id, "weight": s.weight, "reps": s.reps, "rir": s.rir, "date": datetime.utcnow().isoformat()}).execute()
            logged+=1
            # PR check e1RM — строго от эффективной нагрузки (гравитрон инвертирован), skip пустых
            try:
                if s.weight and s.weight > 0 and s.reps and s.reps > 0:
                    is_a = assist_map.get(s.exercise_id, False)
                    from ..math_engine import effective_e1rm as _ee1rm
                    e1rm = _ee1rm(s.weight, s.reps, is_a, bodyweight)
                    rec = sb.table("personal_records").select("e1rm").eq("user_id", req.user_id).eq("exercise_id", s.exercise_id).limit(1).execute()
                    if not rec.data or e1rm > float(rec.data[0]["e1rm"]):
                        sb.table("personal_records").upsert({"user_id": req.user_id, "exercise_id": s.exercise_id, "e1rm": e1rm, "weight": s.weight, "reps": s.reps, "date": str(date.today())}, on_conflict="user_id,exercise_id").execute()
            except Exception:
                pass
        # Тоннаж сессии (эффективный) + дельта + поупражненное сравнение
        session_tonnage = 0.0
        comparison = []
        ex_names = {}
        try:
            r = sb.table("exercises").select("id,name").in_("id", list(last_per_ex.keys())[:50]).execute()
            for row in (r.data or []):
                ex_names[row["id"]] = row.get("name", "Упражнение")
        except Exception:
            pass
        for eid, best in best_per_ex.items():
            is_a = assist_map.get(eid, False)
            eff_w = effective_weight(best["weight"], best["reps"], is_a, bodyweight)
            session_tonnage += eff_w * int(best.get("reps") or 0)
            comparison.append(compare_exercise_to_last(
                eid, ex_names.get(eid, "Упражнение"), best, prev_best_map.get(eid), is_a, bodyweight))
        session_tonnage = round(session_tonnage, 1)
        tonnage_delta = round(session_tonnage - prev_session_tonnage, 1) if prev_session_tonnage is not None else None
        pr_count = sum(1 for c in comparison if c.get("is_pr"))
        for eid, last_set in last_per_ex.items():
            meta = _meta_tuple(fetch_plan_exercise_meta(sb, req.plan_id, eid)) if req.plan_id else None
            if not meta:
                try:
                    r = sb.table("plan_exercises").select("target_reps, exercises(mechanics,cns_load,target_muscle,is_assisted)").eq("exercise_id", eid).limit(1).execute()
                    if r.data:
                        row=r.data[0]
                        exm = row.get("exercises") or {}
                        meta=(row["target_reps"], exm.get("mechanics","compound"), exm.get("cns_load",3), exm.get("target_muscle",""), bool(exm.get("is_assisted",False)))
                except Exception:
                    pass
            if not meta: continue
            tr, mech, cns, mus, _a = meta
            if should_progress(last_set.reps, last_set.rir, parse_target_reps(tr), last_set.weight):
                nw = next_weight(last_set.weight, mech, cns, mus)
                progressions.append({"exercise_id": eid, "old_weight": last_set.weight, "new_weight": nw, "suggestion": suggest_next_set(last_set.rir, last_set.reps, tr, last_set.weight, mech, cns, mus)})
        return {"status": "ok", "logged": logged, "progressions": progressions, "log_id": log_id,
                "comparison": comparison, "session_tonnage": session_tonnage,
                "tonnage_delta": tonnage_delta, "pr_count": pr_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"complete failed: {e}")

@router.post("/cardio-complete")
async def cardio_complete(req: CardioCompleteRequest):
    """Save a hybrid cardio session (LISS+EMOM+LISS) without triggering e1RM / progression."""
    sb = get_supabase()
    try:
        log_data = {
            "user_id": req.user_id,
            "plan_id": req.plan_id,
            "date": str(date.today()),
            "completed": True,
            "session_type": "cardio",
            "total_duration_minutes": req.total_duration_minutes,
            "perceived_effort_rpe": req.perceived_effort_rpe,
            "notes": req.notes or f"LISS+EMOM({req.emom_rounds_completed}r)+LISS Flush"
        }
        ins = sb.table("workout_logs").insert(log_data).execute()
        log_id = ins.data[0]["id"] if ins.data else None
        return {
            "status": "ok",
            "log_id": log_id,
            "message": f"Кардио-сессия сохранена: {req.total_duration_minutes} мин, EMOM {req.emom_rounds_completed}/3, RPE {req.perceived_effort_rpe}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"cardio-complete failed: {e}")

@legacy_router.post("/finish_workout")
async def legacy_finish(req: LegacyFinishRequest):
    mapped = CompleteRequest(user_id=str(req.user_id), day_number=req.day_number, sets=[SetLog(exercise_id=str(s.exercise_id), set_number=s.set_number, weight=s.weight, reps=s.reps, rir=s.rir) for s in req.sets])
    sb = get_supabase()
    try:
        r = sb.table("workout_plans").select("id").limit(1).execute()
        if r.data: mapped.plan_id = r.data[0]["id"]
    except Exception:
        pass
    res = await complete_workout(mapped)
    return {"status": res["status"], "logged": res["logged"], "progressions": res["progressions"]}

@router.get("/active-plan/{user_id}")
async def active_plan(user_id: str):
    sb=get_supabase()
    # find plan via target_user_id or last log
    for cand in [user_id]:
        try:
            r=sb.table("workout_plans").select("*").eq("target_user_id", cand).limit(1).execute()
            if r.data: return r.data[0]
        except: pass
    r=sb.table("workout_plans").select("*").limit(1).execute()
    return r.data[0] if r.data else None

@router.get("/completed-days/{user_id}")
async def completed_days(user_id: str, plan_id: Optional[str] = None, days: int = 7):
    """Статусы дней строго по сохранённому day_number (без смещений):
    {completed_days: {day: {completed, logged_at}}, next_pending_day}."""
    from datetime import timedelta
    sb = get_supabase()
    try:
        since = str(date.today() - timedelta(days=max(1, min(days, 60))))
        q = sb.table("workout_logs").select("day_number,date,created_at").eq("user_id", user_id).eq("completed", True).gte("date", since)
        if plan_id:
            q = q.eq("plan_id", plan_id)
        rows = q.execute().data or []
        done: dict = {}
        for r in rows:
            if r.get("day_number") is None:
                continue
            d = int(r["day_number"])
            stamp = r.get("created_at") or r.get("date")
            prev = done.get(d)
            if prev is None or (stamp and stamp > prev.get("logged_at", "")):
                done[d] = {"completed": True, "logged_at": stamp}
        # next_pending_day: первый день плана, которого нет в completed_days
        plan_days: list = []
        if plan_id:
            try:
                pr = sb.table("plan_exercises").select("day_number").eq("plan_id", plan_id).execute().data or []
                plan_days = sorted({int(x["day_number"]) for x in pr if x.get("day_number") is not None})
            except Exception:
                pass
        nxt = next((d for d in plan_days if d not in done), None)
        return {"completed_days": done, "next_pending_day": nxt,
                "completed_list": sorted(done.keys())}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/plans")
async def list_plans():
    sb=get_supabase()
    return sb.table("workout_plans").select("*").execute().data

class SwapRequest(BaseModel):
    exercise_id: str
    exclude_ids: List[str] = []

@router.post("/swap-exercise")
async def swap_exercise(req: SwapRequest):
    """Instant Machine Swap: same movement_pattern, different equipment"""
    sb=get_supabase()
    cur = sb.table("exercises").select("*").eq("id", req.exercise_id).limit(1).execute()
    if not cur.data:
        raise HTTPException(404, "Exercise not found")
    cur_ex = cur.data[0]
    # candidates with same movement_pattern
    try:
        alts = sb.table("exercises").select("*").eq("movement_pattern", cur_ex["movement_pattern"]).neq("id", req.exercise_id).execute().data
    except Exception as e:
        raise HTTPException(500, str(e))
    # filter excluded (already in day)
    alts = [e for e in alts if e["id"] not in (req.exclude_ids or [])]
    if not alts:
        # fallback same muscle
        try:
            alts = sb.table("exercises").select("*").eq("target_muscle", cur_ex["target_muscle"]).neq("id", req.exercise_id).execute().data
            alts = [e for e in alts if e["id"] not in (req.exclude_ids or [])]
        except: pass
    if not alts:
        raise HTTPException(404, "No alternative found")
    def score(e):
        s=0
        if e["target_muscle"]==cur_ex["target_muscle"]: s-=10
        if e["mechanics"]==cur_ex["mechanics"]: s-=5
        if e["equipment"]!=cur_ex["equipment"]: s-=3  # different equipment good when machine occupied
        s+= e.get("cns_load",3)
        s+= len(e.get("joint_stress") or [])
        return s
    alts.sort(key=score)
    return alts[0]

@router.get("/exercises")
async def list_exercises():
    sb=get_supabase()
    return sb.table("exercises").select("*").execute().data
