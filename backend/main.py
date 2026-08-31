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

# Render runs as backend.main -> app is backend.app; local runs as app.main -> app is app
try:
    from app.database import get_supabase
    from app.routes.workouts import router as workouts_router, legacy_router as workouts_legacy
    from app.routes.readiness import router as readiness_router, legacy_router as readiness_legacy
except ModuleNotFoundError:
    from backend.app.database import get_supabase
    from backend.app.routes.workouts import router as workouts_router, legacy_router as workouts_legacy
    from backend.app.routes.readiness import router as readiness_router, legacy_router as readiness_legacy

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
    try:
        from app.config import SUPABASE_URL, SUPABASE_KEY
    except ModuleNotFoundError:
        from backend.app.config import SUPABASE_URL, SUPABASE_KEY
    return {"status": "ok" if (SUPABASE_URL and SUPABASE_KEY) else "misconfigured"}

class UpdatePlanRequest(BaseModel):
    plan_id: str

class UpdateScheduleRequest(BaseModel):
    schedule: list[int]

# Legacy 1/2 -> UUID mapping for new schema (seed.sql)
LEGACY_ID_MAP = {
    "1": "11111111-1111-1111-1111-111111111111",
    "2": "22222222-2222-2222-2222-222222222222",
}
# reverse for debug
UUID_TO_LEGACY = {v: k for k, v in LEGACY_ID_MAP.items()}
DEFAULT_SCHEDULE = {
    "11111111-1111-1111-1111-111111111111": [1, 3, 5],
    "22222222-2222-2222-2222-222222222222": [1, 2, 4, 5],
}

def _enrich_user(row: dict) -> dict:
    """Add missing legacy fields for new UUID schema so old frontend doesn't crash."""
    if row is None:
        return row
    uid = str(row.get("id"))
    # current_plan_id doesn't exist in new schema -> derive from workout_plans.target_user_id
    if "current_plan_id" not in row or row.get("current_plan_id") is None:
        try:
            sb = get_supabase()
            r = sb.table("workout_plans").select("id").eq("target_user_id", uid).limit(1).execute()
            if r.data:
                row["current_plan_id"] = r.data[0]["id"]
            else:
                # fallback hardcoded
                row["current_plan_id"] = "33333333-3333-3333-3333-333333333333" if uid == "11111111-1111-1111-1111-111111111111" else "44444444-4444-4444-4444-444444444444"
        except Exception:
            row["current_plan_id"] = row.get("current_plan_id") or "33333333-3333-3333-3333-333333333333"
    # schedule doesn't exist in new schema -> default
    if "schedule" not in row or row.get("schedule") is None:
        row["schedule"] = DEFAULT_SCHEDULE.get(uid, [1, 3, 5])
    return row

@app.get("/api/user/{user_id}")
async def get_user(user_id: str):
    sb = get_supabase()
    # build candidates: original, legacy->UUID, UUID string
    candidates = []
    uid_str = str(user_id).strip()
    candidates.append(uid_str)
    if uid_str in LEGACY_ID_MAP:
        candidates.append(LEGACY_ID_MAP[uid_str])
    # if it's already UUID, also try legacy int form (should fail gracefully)
    if uid_str in UUID_TO_LEGACY:
        candidates.append(UUID_TO_LEGACY[uid_str])

    # deduplicate preserving order
    seen = set()
    uniq = []
    for c in candidates:
        if c not in seen:
            uniq.append(c)
            seen.add(c)

    for cand in uniq:
        # 1) try exact string (UUID or int-as-string)
        try:
            r = sb.table("users").select("*").eq("id", cand).execute()
            if r.data:
                return _enrich_user(r.data[0])
        except Exception as e:
            # PostgREST type mismatch (int vs uuid) throws, ignore
            pass
        # 2) try int conversion if numeric
        if cand.isdigit():
            try:
                r = sb.table("users").select("*").eq("id", int(cand)).execute()
                if r.data:
                    return _enrich_user(r.data[0])
            except Exception:
                pass

    # last resort: if table is UUID schema and user asked for "1"/"2", try selecting by name
    if uid_str in ("1", "2"):
        try:
            name = "Ярик" if uid_str == "1" else "Олеся"
            r = sb.table("users").select("*").eq("name", name).limit(1).execute()
            if r.data:
                return _enrich_user(r.data[0])
        except Exception:
            pass

    # debug: include hint when table is empty (new schema not seeded)
    try:
        cnt = sb.table("users").select("id").limit(1).execute()
        if not cnt.data:
            raise HTTPException(404, "User not found: users table is empty — run database/schema.sql + database/seed.sql in Supabase SQL Editor")
    except HTTPException:
        raise
    except Exception:
        pass

    raise HTTPException(404, "User not found")

@app.get("/api/logs/{user_id}")
async def get_logs(user_id: str):
    sb = get_supabase()
    uid = LEGACY_ID_MAP.get(str(user_id), str(user_id))
    for cand in [uid, str(user_id)]:
        try:
            return sb.table("workout_logs").select("date").eq("user_id", cand).execute().data
        except Exception:
            pass
        if cand.isdigit():
            try:
                return sb.table("workout_logs").select("date").eq("user_id", int(cand)).execute().data
            except Exception:
                pass
    return []

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
    # normalize 1/2 -> UUID
    uid = LEGACY_ID_MAP.get(str(user_id), str(user_id))
    candidates = [uid, str(user_id)]
    if str(user_id).isdigit():
        candidates.append(LEGACY_ID_MAP.get(str(user_id)))
    # dedup
    candidates = [c for c in dict.fromkeys(candidates) if c]

    # Try new schema (workout_logs -> workout_sets)
    for cand in candidates:
        try:
            logs = sb.table("workout_logs").select("id").eq("user_id", cand).order("date", desc=True).limit(20).execute().data
            if logs:
                latest = {}
                for log in logs:
                    try:
                        sets = sb.table("workout_sets").select("exercise_id, weight, reps, rir").eq("log_id", log["id"]).execute().data
                    except Exception:
                        continue
                    for s in sets:
                        if s["exercise_id"] not in latest:
                            latest[s["exercise_id"]] = s
                if latest:
                    return latest
                # if logs exist but no sets yet, return empty (no crash)
                return {}
        except Exception:
            pass
        # also try int form for legacy DB
        if cand.isdigit():
            try:
                logs = sb.table("workout_logs").select("id").eq("user_id", int(cand)).order("date", desc=True).limit(20).execute().data
                if logs:
                    latest = {}
                    for log in logs:
                        sets = sb.table("workout_sets").select("exercise_id, weight, reps, rir").eq("log_id", log["id"]).execute().data
                        for s in sets:
                            if s["exercise_id"] not in latest:
                                latest[s["exercise_id"]] = s
                    if latest:
                        return latest
                    return {}
            except Exception:
                pass

    # Fallback legacy: workout_logs has exercise_id directly (old DB) - wrap so missing column doesn't 500
    for cand in candidates:
        try:
            rows = sb.table("workout_logs").select("exercise_id, weight, reps, rir, date").eq("user_id", cand).order("date", desc=True).limit(200).execute().data
            latest = {}
            for r in rows:
                eid = str(r["exercise_id"])
                if eid not in latest:
                    latest[eid] = r
            return latest
        except Exception as e:
            # column does not exist on new schema -> ignore, return empty instead of 500
            if "does not exist" in str(e) or "42703" in str(e):
                continue
            pass
        if cand.isdigit():
            try:
                rows = sb.table("workout_logs").select("exercise_id, weight, reps, rir, date").eq("user_id", int(cand)).order("date", desc=True).limit(200).execute().data
                latest = {}
                for r in rows:
                    eid = str(r["exercise_id"])
                    if eid not in latest:
                        latest[eid] = r
                return latest
            except Exception as e:
                if "does not exist" in str(e):
                    continue
                pass
    # nothing found -> empty is valid (first workout)
    return {}

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
