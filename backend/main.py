"""
Antigravity — Principal Full-Stack [5]
FastAPI entrypoint
"""
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Render запускается как backend.main -> from app... ; локально как main -> from backend.app
try:
    from app.database import get_supabase
    from app.routes.workouts import router as workouts_router, legacy_router as workouts_legacy
    from app.routes.readiness import router as readiness_router, legacy_router as readiness_legacy
    from app.routes.analytics import router as analytics_router
except ModuleNotFoundError:
    from backend.app.database import get_supabase
    from backend.app.routes.workouts import router as workouts_router, legacy_router as workouts_legacy
    from backend.app.routes.readiness import router as readiness_router, legacy_router as readiness_legacy
    from backend.app.routes.analytics import router as analytics_router

app = FastAPI(title="Antigravity", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(workouts_router)
app.include_router(readiness_router)
app.include_router(analytics_router)
app.include_router(workouts_legacy)
app.include_router(readiness_legacy)

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

LEGACY_ID_MAP = {"1":"11111111-1111-1111-1111-111111111111","2":"22222222-2222-2222-2222-222222222222","00000000-0000-0000-0000-000000000001":"11111111-1111-1111-1111-111111111111","00000000-0000-0000-0000-000000000002":"22222222-2222-2222-2222-222222222222"}
UUID_TO_LEGACY = {v:k for k,v in LEGACY_ID_MAP.items()}
DEFAULT_SCHEDULE = {"11111111-1111-1111-1111-111111111111":[1,3,5],"22222222-2222-2222-2222-222222222222":[1,2,4,5],"00000000-0000-0000-0000-000000000001":[1,3,5],"00000000-0000-0000-0000-000000000002":[1,2,4,5]}

def _enrich_user(row: dict) -> dict:
    if not row: return row
    uid=str(row.get("id"))
    if "current_plan_id" not in row or row.get("current_plan_id") is None:
        try:
            sb=get_supabase()
            r=sb.table("workout_plans").select("id").eq("target_user_id", uid).limit(1).execute()
            if r.data: row["current_plan_id"]=r.data[0]["id"]
            else: row["current_plan_id"]="33333333-3333-3333-3333-333333333333" if uid.startswith("111") or uid.startswith("00000000-0000") and "001" in uid else "44444444-4444-4444-4444-444444444444"
        except: row["current_plan_id"]=row.get("current_plan_id") or "33333333-3333-3333-3333-333333333333"
    if "schedule" not in row or row.get("schedule") is None:
        row["schedule"]=DEFAULT_SCHEDULE.get(uid,[1,3,5])
    return row

def _normalize_plan_exercises(rows):
    for r in rows or []:
        if "target_sets" in r and "sets" not in r: r["sets"]=r["target_sets"]
        if "sets" in r and "target_sets" not in r: r["target_sets"]=r["sets"]
        if "target_reps" in r and "reps_target" not in r: r["reps_target"]=r["target_reps"]
        if "reps_target" in r and "target_reps" not in r: r["target_reps"]=r["reps_target"]
        r.setdefault("sets", r.get("target_sets",3))
        r.setdefault("target_sets", r.get("sets",3))
        r.setdefault("reps_target", r.get("target_reps","8-12"))
        r.setdefault("target_reps", r.get("reps_target","8-12"))
        r.setdefault("suggested_method", r.get("suggested_method","normal"))
    return rows

@app.get("/api/user/{user_id}")
async def get_user(user_id: str):
    sb=get_supabase()
    candidates=[str(user_id).strip()]
    if candidates[0] in LEGACY_ID_MAP: candidates.append(LEGACY_ID_MAP[candidates[0]])
    uniq=[]
    for c in candidates:
        if c not in uniq: uniq.append(c)
    for cand in uniq:
        try:
            r=sb.table("users").select("*").eq("id", cand).execute()
            if r.data: return _enrich_user(r.data[0])
        except: pass
        if cand.isdigit():
            try:
                r=sb.table("users").select("*").eq("id", int(cand)).execute()
                if r.data: return _enrich_user(r.data[0])
            except: pass
    if str(user_id) in ("1","2"):
        try:
            name="Ярик" if str(user_id)=="1" else "Олеся"
            r=sb.table("users").select("*").eq("name", name).limit(1).execute()
            if r.data: return _enrich_user(r.data[0])
        except: pass
    try:
        cnt=sb.table("users").select("id").limit(1).execute()
        if not cnt.data: raise HTTPException(404, "User not found: users table is empty — run database/schema.sql + database/seed.sql")
    except HTTPException: raise
    except: pass
    raise HTTPException(404, "User not found")

@app.get("/api/logs/{user_id}")
async def get_logs(user_id: str):
    sb=get_supabase()
    uid=LEGACY_ID_MAP.get(str(user_id), str(user_id))
    for cand in [uid, str(user_id)]:
        try: return sb.table("workout_logs").select("date").eq("user_id", cand).execute().data
        except: pass
        if cand.isdigit():
            try: return sb.table("workout_logs").select("date").eq("user_id", int(cand)).execute().data
            except: pass
    return []

@app.get("/api/plans")
async def get_plans():
    return get_supabase().table("workout_plans").select("*").execute().data

@app.get("/api/plan/{plan_id}")
async def get_plan(plan_id: str):
    sb=get_supabase()
    try:
        plan=sb.table("workout_plans").select("*").eq("id", plan_id).execute()
        if not plan.data:
            try: plan=sb.table("workout_plans").select("*").eq("id", int(plan_id)).execute()
            except: pass
        if not plan.data: raise HTTPException(404, "Plan not found")
        exercises=sb.table("plan_exercises").select("*, exercises(*)").eq("plan_id", plan_id).order("order_index").execute()
        if not exercises.data:
            exercises=sb.table("plan_exercises").select("*, exercises(*)").eq("plan_id", plan_id).order("day_number").execute()
            if not exercises.data and str(plan_id).isdigit():
                try: exercises=sb.table("plan_exercises").select("*, exercises(*)").eq("plan_id", int(plan_id)).order("day_number").execute()
                except: pass
        _normalize_plan_exercises(exercises.data)
        return {"plan": plan.data[0], "exercises": exercises.data}
    except HTTPException: raise
    except Exception as e: raise HTTPException(500, str(e))

@app.get("/api/plan/{plan_id}/day/{day_number}")
async def get_plan_day(plan_id: str, day_number: int):
    sb=get_supabase()
    try:
        data=sb.table("plan_exercises").select("*, exercises(*)").eq("plan_id", plan_id).eq("day_number", day_number).order("order_index").execute().data
        return _normalize_plan_exercises(data)
    except:
        try:
            data=sb.table("plan_exercises").select("*, exercises(*)").eq("plan_id", int(plan_id)).eq("day_number", day_number).execute().data
            return _normalize_plan_exercises(data)
        except Exception as e: raise HTTPException(500, str(e))

@app.get("/api/exercises")
async def get_all_exercises():
    return get_supabase().table("exercises").select("*").execute().data

@app.get("/api/last_weights/{user_id}")
async def get_last_weights(user_id: str):
    sb=get_supabase()
    uid=LEGACY_ID_MAP.get(str(user_id), str(user_id))
    candidates=[uid, str(user_id)]
    candidates=[c for c in dict.fromkeys(candidates) if c]
    for cand in candidates:
        try:
            logs=sb.table("workout_logs").select("id").eq("user_id", cand).order("date", desc=True).limit(20).execute().data
            if logs:
                latest={}
                for log in logs:
                    try: sets=sb.table("workout_sets").select("exercise_id, weight, reps, rir").eq("log_id", log["id"]).execute().data
                    except: continue
                    for s in sets:
                        if s["exercise_id"] not in latest: latest[s["exercise_id"]]=s
                if latest: return latest
                return {}
        except: pass
    for cand in candidates:
        try:
            rows=sb.table("workout_logs").select("exercise_id, weight, reps, rir, date").eq("user_id", cand).order("date", desc=True).limit(200).execute().data
            latest={}
            for r in rows:
                eid=str(r["exercise_id"])
                if eid not in latest: latest[eid]=r
            return latest
        except Exception as e:
            if "does not exist" in str(e) or "42703" in str(e): continue
            pass
    return {}

@app.patch("/api/user/{user_id}/schedule")
async def update_schedule(user_id: str, req: UpdateScheduleRequest):
    sb=get_supabase()
    try: sb.table("users").update({"schedule": req.schedule}).eq("id", user_id).execute()
    except:
        try: sb.table("users").update({"schedule": req.schedule}).eq("id", int(user_id)).execute()
        except: pass
    return {"status":"ok"}

@app.patch("/api/user/{user_id}/plan")
async def update_user_plan(user_id: str, req: UpdatePlanRequest):
    sb=get_supabase()
    try:
        r=sb.table("users").update({"current_plan_id": req.plan_id}).eq("id", user_id).execute()
        if not r.data: r=sb.table("users").update({"current_plan_id": req.plan_id}).eq("id", int(user_id)).execute()
        return {"status":"ok","data":r.data}
    except: return {"status":"ok"}

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
ROOT_INDEX = Path(__file__).parent.parent / "index.html"
if FRONTEND_DIR.exists():
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")

@app.get("/")
async def root():
    new_index = FRONTEND_DIR / "index.html"
    if new_index.exists(): return FileResponse(str(new_index))
    if ROOT_INDEX.exists(): return FileResponse(str(ROOT_INDEX))
    return {"message":"Antigravity API running","docs":"/docs"}

if __name__=="__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT","8000")))
