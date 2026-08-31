from datetime import date, datetime
from typing import List, Literal, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..database import get_supabase
from ..progression import parse_target_reps, should_progress, next_weight, suggest_next_set
from ..math_engine import warmup_sets, epley_e1rm, plate_breakdown

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
        r = sb.table("plan_exercises").select("target_reps, exercises(mechanics, cns_load, target_muscle)").eq("plan_id", plan_id).eq("exercise_id", exercise_id).limit(1).execute()
        if r.data:
            row = r.data[0]
            return row["target_reps"], row["exercises"]["mechanics"], row["exercises"]["cns_load"], row["exercises"]["target_muscle"]
    except Exception:
        pass
    return None

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
            meta = fetch_plan_exercise_meta(sb, req.plan_id, req.exercise_id)
            if meta:
                tr, mech, cns, mus = meta
        except Exception:
            pass
    tr = tr or "8-12"
    suggestion = suggest_next_set(req.rir, req.reps, tr, req.weight, mech, cns, mus)
    warmup = warmup_sets(suggestion["next_weight"] if suggestion["action"]=="increase" else req.weight)
    plates = plate_breakdown(suggestion["next_weight"])
    return {**suggestion, "warmup": warmup, "plates": plates, "target_reps": tr}

@router.post("/complete")
async def complete_workout(req: CompleteRequest):
    sb = get_supabase()
    try:
        log_id = None
        try:
            ins = sb.table("workout_logs").insert({"user_id": req.user_id, "plan_id": req.plan_id, "date": str(date.today()), "completed": True}).execute()
            log_id = ins.data[0]["id"] if ins.data else None
        except Exception:
            log_id = None
        progressions=[]
        logged=0
        last_per_ex={}
        for s in req.sets:
            last_per_ex[s.exercise_id]=s
        for s in req.sets:
            if log_id:
                try:
                    sb.table("workout_sets").insert({"log_id": log_id, "exercise_id": s.exercise_id, "set_number": s.set_number, "set_type": s.set_type, "weight": s.weight, "reps": s.reps, "rir": s.rir}).execute()
                except Exception:
                    sb.table("workout_logs").insert({"user_id": req.user_id, "exercise_id": s.exercise_id, "weight": s.weight, "reps": s.reps, "rir": s.rir, "date": datetime.utcnow().isoformat()}).execute()
            else:
                sb.table("workout_logs").insert({"user_id": req.user_id, "exercise_id": s.exercise_id, "weight": s.weight, "reps": s.reps, "rir": s.rir, "date": datetime.utcnow().isoformat()}).execute()
            logged+=1
            # PR check e1RM
            try:
                e1rm = epley_e1rm(s.weight, s.reps)
                rec = sb.table("personal_records").select("e1rm").eq("user_id", req.user_id).eq("exercise_id", s.exercise_id).limit(1).execute()
                if not rec.data or e1rm > float(rec.data[0]["e1rm"]):
                    sb.table("personal_records").upsert({"user_id": req.user_id, "exercise_id": s.exercise_id, "e1rm": e1rm, "weight": s.weight, "reps": s.reps, "date": str(date.today())}, on_conflict="user_id,exercise_id").execute()
            except Exception:
                pass
        for eid, last_set in last_per_ex.items():
            meta = fetch_plan_exercise_meta(sb, req.plan_id, eid) if req.plan_id else None
            if not meta:
                try:
                    r = sb.table("plan_exercises").select("target_reps, exercises(mechanics,cns_load,target_muscle)").eq("exercise_id", eid).limit(1).execute()
                    if r.data:
                        row=r.data[0]
                        meta=(row["target_reps"], row["exercises"]["mechanics"], row["exercises"]["cns_load"], row["exercises"]["target_muscle"])
                except Exception:
                    pass
            if not meta: continue
            tr, mech, cns, mus = meta
            if should_progress(last_set.reps, last_set.rir, parse_target_reps(tr), last_set.weight):
                nw = next_weight(last_set.weight, mech, cns, mus)
                progressions.append({"exercise_id": eid, "old_weight": last_set.weight, "new_weight": nw, "suggestion": suggest_next_set(last_set.rir, last_set.reps, tr, last_set.weight, mech, cns, mus)})
        return {"status": "ok", "logged": logged, "progressions": progressions, "log_id": log_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"complete failed: {e}")

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
