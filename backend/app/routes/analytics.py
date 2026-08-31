from fastapi import APIRouter, HTTPException
from ..database import get_supabase
from ..math_engine import deload_check, mev_mav_status, epley_e1rm
from datetime import date, timedelta

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/weekly-volume/{user_id}")
async def weekly_volume(user_id: str):
    sb=get_supabase()
    try:
        week_ago = str(date.today() - timedelta(days=7))
        logs = sb.table("workout_logs").select("id").eq("user_id", user_id).gte("date", week_ago).execute().data
        vol={}
        for log in logs:
            sets = sb.table("workout_sets").select("exercise_id, exercises(target_muscle)").eq("log_id", log["id"]).execute().data
            for s in sets:
                mus = s["exercises"]["target_muscle"] if s.get("exercises") else "unknown"
                vol[mus]=vol.get(mus,0)+1
        # status
        status={m: mev_mav_status(c,m) for m,c in vol.items()}
        return {"volume": vol, "status": status}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/records/{user_id}")
async def records(user_id: str):
    sb=get_supabase()
    try:
        recs = sb.table("personal_records").select("*, exercises(name)").eq("user_id", user_id).execute().data
        return recs
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/check-deload/{user_id}")
async def check_deload(user_id: str):
    sb=get_supabase()
    try:
        readiness = sb.table("readiness_logs").select("readiness_score").eq("user_id", user_id).order("date", desc=True).limit(5).execute().data
        scores=[float(r["readiness_score"]) for r in readiness if r.get("readiness_score") is not None]
        # volume trend last 3 weeks
        week_vol=[]
        for w in range(3):
            start = str(date.today() - timedelta(days=7*(w+1)))
            end = str(date.today() - timedelta(days=7*w))
            logs = sb.table("workout_logs").select("id").eq("user_id", user_id).gte("date", start).lt("date", end).execute().data
            cnt=0
            for log in logs:
                cnt+= len(sb.table("workout_sets").select("id").eq("log_id", log["id"]).execute().data)
            week_vol.insert(0,cnt)
        res = deload_check(scores, week_vol)
        return res
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/e1rm")
async def calc_e1rm(weight: float, reps: int):
    return {"e1rm": epley_e1rm(weight, reps), "plates": __import__('backend.app.math_engine', fromlist=['plate_breakdown']).plate_breakdown(weight) if False else None}
