from datetime import date, datetime
from typing import List, Literal, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..database import get_supabase
from ..progression import parse_target_reps, should_progress, next_weight

router = APIRouter(prefix="/api/workouts", tags=["workouts"])
legacy_router = APIRouter(prefix="/api", tags=["legacy"])

class SetLog(BaseModel):
    exercise_id: str  # UUID string (supports int legacy as str)
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

class LegacySetLog(BaseModel):
    exercise_id: str  # accept UUID or int string
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
    # legacy fallback
    try:
        r = sb.table("plan_exercises").select("reps_target, exercises(mechanics, target_muscle)").eq("plan_id", int(plan_id)).eq("exercise_id", int(exercise_id)).limit(1).execute()
        # legacy plan_exercises has reps_target not target_reps, and no cns_load
        if r.data:
            row = r.data[0]
            rt = row.get("reps_target") or row.get("target_reps")
            ex = row.get("exercises", {})
            return rt, ex.get("mechanics","compound"), ex.get("cns_load",3), ex.get("target_muscle","")
    except Exception:
        pass
    return None

@router.post("/complete")
async def complete_workout(req: CompleteRequest):
    sb = get_supabase()
    try:
        # create workout_log
        log_id = None
        try:
            # try UUID schema first
            ins = sb.table("workout_logs").insert({
                "user_id": req.user_id,
                "plan_id": req.plan_id,
                "date": str(date.today()),
                "completed": True
            }).execute()
            log_id = ins.data[0]["id"] if ins.data else None
        except Exception as e:
            # legacy schema: workout_logs(user_id, exercise_id, weight, reps, rir, date) - no log_id
            # fallback to legacy direct insert per set
            log_id = None

        progressions = []
        logged = 0
        # group last set per exercise
        last_per_ex = {}
        for s in req.sets:
            last_per_ex[s.exercise_id] = s

        for s in req.sets:
            # insert set
            if log_id:
                try:
                    sb.table("workout_sets").insert({
                        "log_id": log_id,
                        "exercise_id": s.exercise_id,
                        "set_number": s.set_number,
                        "set_type": s.set_type,
                        "weight": s.weight,
                        "reps": s.reps,
                        "rir": s.rir
                    }).execute()
                except Exception as e:
                    # legacy fallback: insert into workout_logs directly
                    sb.table("workout_logs").insert({
                        "user_id": int(req.user_id) if str(req.user_id).isdigit() else None,
                        "exercise_id": int(s.exercise_id) if str(s.exercise_id).isdigit() else None,
                        "weight": s.weight,
                        "reps": s.reps,
                        "rir": s.rir,
                        "date": datetime.utcnow().isoformat()
                    }).execute()
            else:
                # no log_id (legacy) -> direct
                try:
                    sb.table("workout_logs").insert({
                        "user_id": int(req.user_id) if str(req.user_id).isdigit() else req.user_id,
                        "exercise_id": int(s.exercise_id) if str(s.exercise_id).isdigit() else s.exercise_id,
                        "weight": s.weight,
                        "reps": s.reps,
                        "rir": s.rir,
                        "date": datetime.utcnow().isoformat()
                    }).execute()
                except Exception:
                    # try UUID string
                    sb.table("workout_logs").insert({
                        "user_id": req.user_id,
                        "exercise_id": s.exercise_id,
                        "weight": s.weight,
                        "reps": s.reps,
                        "rir": s.rir,
                        "date": datetime.utcnow().isoformat()
                    }).execute()
            logged += 1

        # progression
        for eid, last_set in last_per_ex.items():
            meta = None
            if req.plan_id:
                meta = fetch_plan_exercise_meta(sb, req.plan_id, eid)
            if not meta:
                # try without plan_id: find any plan_exercise for this exercise
                try:
                    r = sb.table("plan_exercises").select("target_reps, exercises(mechanics,cns_load,target_muscle)").eq("exercise_id", eid).limit(1).execute()
                    if r.data:
                        row = r.data[0]
                        meta = (row["target_reps"], row["exercises"]["mechanics"], row["exercises"]["cns_load"], row["exercises"]["target_muscle"])
                except Exception:
                    pass
            if not meta:
                continue
            target_reps_str, mechanics, cns_load, target_muscle = meta
            tr = parse_target_reps(target_reps_str)
            if should_progress(last_set.reps, last_set.rir, tr, last_set.weight):
                nw = next_weight(last_set.weight, mechanics, cns_load, target_muscle)
                progressions.append({"exercise_id": eid, "old_weight": last_set.weight, "new_weight": nw})

        return {"status": "ok", "logged": logged, "progressions": progressions, "log_id": log_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"complete failed: {e}")

# legacy alias: POST /api/finish_workout (int ids)
@legacy_router.post("/finish_workout")
async def legacy_finish(req: LegacyFinishRequest):
    # adapt to new CompleteRequest
    mapped = CompleteRequest(
        user_id=str(req.user_id),
        day_number=req.day_number,
        sets=[SetLog(exercise_id=str(s.exercise_id), set_number=s.set_number, weight=s.weight, reps=s.reps, rir=s.rir) for s in req.sets]
    )
    # need plan_id: fetch user current_plan_id if exists
    sb = get_supabase()
    try:
        # try legacy users table (int id)
        r = sb.table("users").select("current_plan_id").eq("id", req.user_id).execute()
        if r.data and r.data[0].get("current_plan_id"):
            mapped.plan_id = str(r.data[0]["current_plan_id"])
        else:
            # try UUID users
            r2 = sb.table("users").select("id").limit(1).execute()
            pass
    except Exception:
        pass
    # also try new users table
    if not mapped.plan_id:
        try:
            # if users is UUID based, int lookup fails, try fallback: get any plan
            r = sb.table("workout_plans").select("id").limit(1).execute()
            if r.data:
                mapped.plan_id = r.data[0]["id"]
        except Exception:
            pass
    res = await complete_workout(mapped)
    # legacy response expects {status, logged, progressions}
    return {"status": res["status"], "logged": res["logged"], "progressions": res["progressions"]}

@router.get("/plans")
async def list_plans():
    sb = get_supabase()
    try:
        return sb.table("workout_plans").select("*").execute().data
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/exercises")
async def list_exercises():
    sb = get_supabase()
    try:
        return sb.table("exercises").select("*").execute().data
    except Exception as e:
        raise HTTPException(500, str(e))
