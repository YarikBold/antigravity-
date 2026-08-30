"""
Antigravity - AI Strength Training Tracker
FastAPI Backend
"""

import json
import os
from datetime import datetime
from typing import Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from supabase import create_client, Client

load_dotenv()

# --------------- Config ---------------
SUPABASE_URL     = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY     = os.getenv("SUPABASE_KEY", "")
OPENROUTER_KEY   = os.getenv("OPENROUTER_API_KEY", "")

# Lazy Supabase client — не падаем при старте если env пустой
_supabase: Client | None = None

def get_supabase() -> Client:
    global _supabase
    if _supabase is not None:
        return _supabase
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise HTTPException(500, "Server misconfigured: SUPABASE_URL / SUPABASE_KEY missing. Check Render Environment Variables.")
    try:
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        raise HTTPException(500, f"Failed to init Supabase: {e}")
    return _supabase

# Для обратной совместимости — прокси свойство
class _SupabaseProxy:
    def __getattr__(self, name):
        return getattr(get_supabase(), name)
supabase = _SupabaseProxy()  # type: ignore

app = FastAPI(title="Antigravity", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------- Pydantic Models ---------------
class SetLog(BaseModel):
    exercise_id: int
    set_number: int
    weight: float
    reps: int
    rir: int


class FinishWorkoutRequest(BaseModel):
    user_id: int
    day_number: int
    sets: list[SetLog]


class ReadinessRequest(BaseModel):
    user_id: int
    plan_id: int
    day_number: int
    sore_muscles: list[str]
    pain_level: int          # 1-10


class UpdatePlanRequest(BaseModel):
    plan_id: int

class UpdateScheduleRequest(BaseModel):
    schedule: list[int]


# --------------- Endpoints ---------------

@app.get("/")
async def root():
    return FileResponse("index.html")


@app.get("/health")
async def health():
    ok = bool(SUPABASE_URL and SUPABASE_KEY)
    return {"status": "ok" if ok else "misconfigured", "supabase_configured": ok}

@app.get("/api/user/{user_id}")
async def get_user(user_id: int):
    try:
        r = get_supabase().table("users").select("*").eq("id", user_id).execute()
        if not r.data:
            raise HTTPException(404, "User not found")
        return r.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"get_user failed: {e}")


@app.get("/api/logs/{user_id}")
async def get_logs(user_id: int):
    try:
        return get_supabase().table("workout_logs").select("date").eq("user_id", user_id).execute().data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"get_logs failed: {e}")

@app.get("/api/plans")
async def get_plans():
    try:
        return get_supabase().table("workout_plans").select("*").execute().data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"get_plans failed: {e}")


@app.get("/api/plan/{plan_id}")
async def get_plan(plan_id: int):
    try:
        sb = get_supabase()
        plan = sb.table("workout_plans").select("*").eq("id", plan_id).execute()
        if not plan.data:
            raise HTTPException(404, "Plan not found")
        exercises = (
            sb.table("plan_exercises")
            .select("*, exercises(*)")
            .eq("plan_id", plan_id)
            .order("day_number")
            .execute()
        )
        return {"plan": plan.data[0], "exercises": exercises.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"get_plan failed: {e}")


@app.get("/api/plan/{plan_id}/day/{day_number}")
async def get_plan_day(plan_id: int, day_number: int):
    try:
        return (
            get_supabase().table("plan_exercises")
            .select("*, exercises(*)")
            .eq("plan_id", plan_id)
            .eq("day_number", day_number)
            .execute()
            .data
        )
    except Exception as e:
        raise HTTPException(500, f"get_plan_day failed: {e}")


@app.get("/api/exercises")
async def get_all_exercises():
    try:
        return get_supabase().table("exercises").select("*").execute().data
    except Exception as e:
        raise HTTPException(500, f"get_all_exercises failed: {e}")


@app.get("/api/last_weights/{user_id}")
async def get_last_weights(user_id: int):
    """Most recent log per exercise for a given user."""
    try:
        rows = (
            get_supabase().table("workout_logs")
            .select("exercise_id, weight, reps, rir, date")
            .eq("user_id", user_id)
            .order("date", desc=True)
            .limit(200)
            .execute()
            .data
        )
        latest: dict = {}
        for row in rows:
            eid = row["exercise_id"]
            if eid not in latest:
                latest[eid] = row
        return latest
    except Exception as e:
        raise HTTPException(500, f"get_last_weights failed: {e}")


@app.patch("/api/user/{user_id}/schedule")
async def update_schedule(user_id: int, req: UpdateScheduleRequest):
    try:
        get_supabase().table("users").update({"schedule": req.schedule}).eq("id", user_id).execute()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(500, f"update_schedule failed: {e}")

@app.patch("/api/user/{user_id}/plan")
async def update_user_plan(user_id: int, req: UpdatePlanRequest):
    try:
        r = (
            get_supabase().table("users")
            .update({"current_plan_id": req.plan_id})
            .eq("id", user_id)
            .execute()
        )
        return {"status": "ok", "data": r.data}
    except Exception as e:
        raise HTTPException(500, f"update_user_plan failed: {e}")


# ---------- Finish Workout + Progression ----------

@app.post("/api/finish_workout")
async def finish_workout(req: FinishWorkoutRequest):
    """Log every set, then check progression per exercise."""
    try:
        sb = get_supabase()
        progressions = []
        logged_count = 0

        user = sb.table("users").select("current_plan_id").eq("id", req.user_id).execute()
        plan_id = user.data[0]["current_plan_id"] if user.data else None

        # 1. Log all sets
        for s in req.sets:
            sb.table("workout_logs").insert({
                "user_id":     req.user_id,
                "exercise_id": s.exercise_id,
                "weight":      s.weight,
                "reps":        s.reps,
                "rir":         s.rir,
                "date":        datetime.utcnow().isoformat(),
            }).execute()
            logged_count += 1

        # 2. Progression check (last set per exercise)
        exercise_sets: dict[int, list[SetLog]] = {}
        for s in req.sets:
            exercise_sets.setdefault(s.exercise_id, []).append(s)

        if plan_id:
            for eid, sets_list in exercise_sets.items():
                last_set = sets_list[-1]

                plan_ex = (
                    sb.table("plan_exercises")
                    .select("reps_target")
                    .eq("plan_id", plan_id)
                    .eq("exercise_id", eid)
                    .limit(1)
                    .execute()
                )
                if not plan_ex.data:
                    continue

                rt = plan_ex.data[0]["reps_target"]
                # ТЗ: цель = верхняя граница диапазона (8-12 -> 12)
                target_reps = int(rt.split("-")[1]) if "-" in rt else int(rt)

                # ТЗ строго: RIR >= 1 и выполнены целевые повторения -> +2.5 кг
                if last_set.rir >= 1 and last_set.reps >= target_reps and last_set.weight > 0:
                    new_w = round(last_set.weight + 2.5, 2)
                    progressions.append({
                        "exercise_id": eid,
                        "old_weight":  last_set.weight,
                        "new_weight":  new_w,
                    })

        return {"status": "ok", "logged": logged_count, "progressions": progressions}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"finish_workout failed: {e}")


# ---------- AI Readiness Check ----------

@app.post("/api/check_readiness")
async def check_readiness(req: ReadinessRequest):
    if req.pain_level < 7:
        return {"status": "ok", "message": "Готов к тренировке!", "substitutions": []}

    sb = get_supabase()
    day_ex = (
        sb.table("plan_exercises")
        .select("*, exercises(*)")
        .eq("plan_id", req.plan_id)
        .eq("day_number", req.day_number)
        .execute()
    )
    all_ex = sb.table("exercises").select("*").execute()

    today_str = "\n".join([
        f"- ID {e['exercise_id']}: {e['exercises']['name']} "
        f"(muscle: {e['exercises']['target_muscle']}, type: {e['exercises']['movement_pattern']})"
        for e in day_ex.data
    ])
    all_str = "\n".join([
        f"- ID {e['id']}: {e['name']} "
        f"(muscle: {e['target_muscle']}, type: {e['movement_pattern']})"
        for e in all_ex.data
    ])

    prompt = (
        f"User reports DOMS pain level {req.pain_level}/10 "
        f"in: {', '.join(req.sore_muscles)}.\n\n"
        f"Today's exercises:\n{today_str}\n\n"
        f"All available exercises:\n{all_str}\n\n"
        f"Find exercises that stress the sore muscles and suggest "
        f"substitutions from the available list.\n\n"
        f"Reply STRICTLY as JSON:\n"
        f'{{"substitutions":[{{"original_exercise_id":<int>,'
        f'"replacement_exercise_id":<int>,"reason":"<reason>"}}],'
        f'"general_advice":"<advice>"}}'
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "stealth/ox-alpha",
                    "messages": [
                        {"role": "system", "content": "You are a sports physiologist. Reply strictly in JSON, no markdown."},
                        {"role": "user",   "content": prompt},
                    ],
                    "temperature": 0.3,
                },
            )
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            result = json.loads(content.strip())
            return {"status": "modified", **result}
    except Exception as e:
        return {
            "status": "error",
            "message": f"AI unavailable: {str(e)}",
            "substitutions": [],
        }


# --------------- Run ---------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)