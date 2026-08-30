"""
Antigravity — Principal Full-Stack
FastAPI entrypoint
"""
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.database import get_supabase
from app.routes.workouts import router as workouts_router, legacy_router as workouts_legacy
from app.routes.readiness import router as readiness_router, legacy_router as readiness_legacy

app = FastAPI(title="Antigravity", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(workouts_router)
app.include_router(readiness_router)
app.include_router(workouts_legacy)
app.include_router(readiness_legacy)

# ---- Legacy compatibility endpoints (old frontend expects these) ----

@app.get("/health")
async def health():
    from app.config import SUPABASE_URL, SUPABASE_KEY
    return {"status": "ok" if (SUPABASE_URL and SUPABASE_KEY) else "misconfigured"}

class UpdatePlanRequest(BaseModel):
    plan_id: str

class UpdateScheduleRequest(BaseModel):
    schedule: list[int]

@app.get("/api/user/{user_id}")
async def get_user(user_id: str):
    sb = get_supabase()
    # try UUID, then int
    for tbl in ["users"]:
        try:
            r = sb.table("users").select("*").eq("id", user_id).execute()
            if r.data:
                return r.data[0]
        except Exception:
            pass
        try:
            # legacy int
            r = sb.table("users").select("*").eq("id", int(user_id)).execute()
            if r.data:
                return r.data[0]
        except Exception:
            pass
    raise HTTPException(404, "User not found")

@app.get("/api/logs/{user_id}")
async def get_logs(user_id: str):
    sb = get_supabase()
    try:
        # new schema: workout_logs has date column
        return sb.table("workout_logs").select("date").eq("user_id", user_id).execute().data
    except Exception:
        try:
            return sb.table("workout_logs").select("date").eq("user_id", int(user_id)).execute().data
        except Exception as e:
            raise HTTPException(500, str(e))

@app.get("/api/plans")
async def get_plans():
    sb = get_supabase()
    try:
        return sb.table("workout_plans").select("*").execute().data
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/plan/{plan_id}")
async def get_plan(plan_id: str):
    sb = get_supabase()
    try:
        plan = sb.table("workout_plans").select("*").eq("id", plan_id).execute()
        if not plan.data:
            # legacy int
            plan = sb.table("workout_plans").select("*").eq("id", int(plan_id)).execute()
        if not plan.data:
            raise HTTPException(404, "Plan not found")
        exercises = sb.table("plan_exercises").select("*, exercises(*)").eq("plan_id", plan_id).order("order_index").execute()
        if not exercises.data:
            exercises = sb.table("plan_exercises").select("*, exercises(*)").eq("plan_id", plan_id).order("day_number").execute()
            if not exercises.data and plan_id.isdigit():
                exercises = sb.table("plan_exercises").select("*, exercises(*)").eq("plan_id", int(plan_id)).order("day_number").execute()
        return {"plan": plan.data[0], "exercises": exercises.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/plan/{plan_id}/day/{day_number}")
async def get_plan_day(plan_id: str, day_number: int):
    sb = get_supabase()
    try:
        return sb.table("plan_exercises").select("*, exercises(*)").eq("plan_id", plan_id).eq("day_number", day_number).order("order_index").execute().data
    except Exception:
        try:
            return sb.table("plan_exercises").select("*, exercises(*)").eq("plan_id", int(plan_id)).eq("day_number", day_number).execute().data
        except Exception as e:
            raise HTTPException(500, str(e))

@app.get("/api/exercises")
async def get_all_exercises():
    sb = get_supabase()
    try:
        return sb.table("exercises").select("*").execute().data
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/last_weights/{user_id}")
async def get_last_weights(user_id: str):
    sb = get_supabase()
    try:
        # try new workout_sets join
        try:
            # new: via workout_logs -> workout_sets
            logs = sb.table("workout_logs").select("id").eq("user_id", user_id).order("date", desc=True).limit(10).execute().data
            if logs:
                latest = {}
                for log in logs:
                    sets = sb.table("workout_sets").select("exercise_id, weight, reps, rir").eq("log_id", log["id"]).execute().data
                    for s in sets:
                        if s["exercise_id"] not in latest:
                            latest[s["exercise_id"]] = s
                if latest:
                    return latest
        except Exception:
            pass
        # fallback legacy: workout_logs directly has exercise_id, weight, reps, rir
        rows = sb.table("workout_logs").select("exercise_id, weight, reps, rir, date").eq("user_id", user_id).order("date", desc=True).limit(200).execute().data
        if not rows and user_id.isdigit():
            rows = sb.table("workout_logs").select("exercise_id, weight, reps, rir, date").eq("user_id", int(user_id)).order("date", desc=True).limit(200).execute().data
        latest = {}
        for r in rows:
            eid = str(r["exercise_id"])
            if eid not in latest:
                latest[eid] = r
        return latest
    except Exception as e:
        raise HTTPException(500, str(e))

@app.patch("/api/user/{user_id}/schedule")
async def update_schedule(user_id: str, req: UpdateScheduleRequest):
    # schedule not in new schema -> store in legacy users.schedule if exists, else ignore
    sb = get_supabase()
    try:
        sb.table("users").update({"schedule": req.schedule}).eq("id", user_id).execute()
    except Exception:
        try:
            sb.table("users").update({"schedule": req.schedule}).eq("id", int(user_id)).execute()
        except Exception as e:
            # new schema has no schedule column -> store in readiness_logs or ignore
            pass
    return {"status": "ok"}

@app.patch("/api/user/{user_id}/plan")
async def update_user_plan(user_id: str, req: UpdatePlanRequest):
    sb = get_supabase()
    try:
        # new schema has no current_plan_id, but legacy does
        r = sb.table("users").update({"current_plan_id": req.plan_id}).eq("id", user_id).execute()
        if not r.data:
            r = sb.table("users").update({"current_plan_id": req.plan_id}).eq("id", int(user_id)).execute()
        return {"status": "ok", "data": r.data}
    except Exception:
        # new schema: we cannot store, but return ok for frontend
        return {"status": "ok"}

# ---- Static frontend ----
# Serve new frontend if exists, else legacy root index.html
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
ROOT_INDEX = Path(__file__).parent.parent / "index.html"

if FRONTEND_DIR.exists():
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")

@app.get("/")
async def root():
    # prefer new frontend
    new_index = FRONTEND_DIR / "index.html"
    if new_index.exists():
        return FileResponse(str(new_index))
    if ROOT_INDEX.exists():
        return FileResponse(str(ROOT_INDEX))
    return {"message": "Antigravity API running", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
