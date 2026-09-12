from datetime import date
from calendar import monthrange
from typing import Optional
from fastapi import APIRouter, HTTPException
from ..database import get_supabase

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/calendar/{user_id}")
async def history_calendar(user_id: str, month: Optional[int] = None, year: Optional[int] = None):
    """Календарь завершённых тренировок за месяц: даты с зелёными точками + карточки сессий."""
    sb = get_supabase()
    today = date.today()
    m = month if month and 1 <= month <= 12 else today.month
    y = year if year and 2020 <= year <= 2100 else today.year

    first_day = date(y, m, 1)
    last_day = date(y, m, monthrange(y, m)[1])

    try:
        rows = (
            sb.table("workout_logs")
            .select("id, date, day_number, plan_id, session_type, total_duration_minutes, created_at")
            .eq("user_id", user_id)
            .eq("completed", True)
            .gte("date", str(first_day))
            .lte("date", str(last_day))
            .order("date", desc=False)
            .execute()
            .data or []
        )
    except Exception as e:
        raise HTTPException(500, f"history calendar: {e}")

            completed_dates = sorted({str(r["date"])[:10] for r in rows})

    plan_cache = {}
    sessions = []
    for r in rows:
        pid = r.get("plan_id")
        plan_name = "Тренировка"
        if pid:
            if pid not in plan_cache:
                try:
                    pr = sb.table("workout_plans").select("name").eq("id", pid).limit(1).execute()
                    plan_cache[pid] = pr.data[0]["name"] if pr.data else "Тренировка"
                except Exception:
                    plan_cache[pid] = "Тренировка"
            plan_name = plan_cache[pid]

        log_id = r["id"]
        ex_count = 0
        set_count = 0
        try:
            sets = sb.table("workout_sets").select("exercise_id, set_number").eq("log_id", log_id).execute().data or []
            set_count = len(sets)
            ex_count = len({s["exercise_id"] for s in sets})
        except Exception:
            pass

        duration = r.get("total_duration_minutes")
        if not duration and set_count > 0:
            duration = max(20, set_count * 3)

        sessions.append({
            "log_id": log_id,
            "date": str(r["date"])[:10],
            "day_number": r.get("day_number"),
            "plan_name": plan_name,
            "plan_id": pid,
            "session_type": r.get("session_type", "strength"),
            "total_duration_minutes": duration,
            "exercise_count": ex_count,
            "set_count": set_count,
        })

    return {
        "month": m,
        "year": y,
        "completed_dates": completed_dates,
        "sessions": sessions,
    }


@router.get("/session/{log_id}")
async def history_session(log_id: str):
    """Read-Only детали тренировки: список упражнений с зафиксированными сетами."""
    sb = get_supabase()
    try:
        log_r = sb.table("workout_logs").select("*").eq("id", log_id).limit(1).execute()
        if not log_r.data:
            raise HTTPException(404, "Session not found")
        log = log_r.data[0]

        plan_name = "Тренировка"
        if log.get("plan_id"):
            try:
                pr = sb.table("workout_plans").select("name").eq("id", log["plan_id"]).limit(1).execute()
                if pr.data:
                    plan_name = pr.data[0]["name"]
            except Exception:
                pass

        sets = (
            sb.table("workout_sets")
            .select("exercise_id, set_number, weight, reps, rir, set_type, duration_seconds, completed_rounds")
            .eq("log_id", log_id)
            .order("set_number")
            .execute()
            .data or []
        )

        ex_ids = list({s["exercise_id"] for s in sets})
        ex_map = {}
        for i in range(0, len(ex_ids), 20):
            chunk = ex_ids[i:i + 20]
            try:
                r = sb.table("exercises").select("id, name, is_assisted, target_muscle, equipment, movement_pattern").in_("id", chunk).execute()
                for row in (r.data or []):
                    ex_map[row["id"]] = row
            except Exception:
                pass

        exercises_grouped = {}
        exercise_order = []
        for s in sets:
            eid = s["exercise_id"]
            if eid not in exercises_grouped:
                exercises_grouped[eid] = []
                exercise_order.append(eid)
            exercises_grouped[eid].append({
                "set_number": s["set_number"],
                "weight": s.get("weight"),
                "reps": s.get("reps"),
                "rir": s.get("rir"),
                "set_type": s.get("set_type", "normal"),
                "duration_seconds": s.get("duration_seconds"),
                "completed_rounds": s.get("completed_rounds"),
            })

        exercises = []
        for eid in exercise_order:
            info = ex_map.get(eid, {})
            exercises.append({
                "exercise_id": eid,
                "name": info.get("name", "Упражнение"),
                "is_assisted": bool(info.get("is_assisted", False)),
                "target_muscle": info.get("target_muscle", ""),
                "equipment": info.get("equipment", ""),
                "movement_pattern": info.get("movement_pattern", ""),
                "sets": exercises_grouped[eid],
            })

        return {
            "log_id": log_id,
            "date": str(log["date"])[:10],
            "day_number": log.get("day_number"),
            "plan_name": plan_name,
            "plan_id": log.get("plan_id"),
            "session_type": log.get("session_type", "strength"),
            "total_duration_minutes": log.get("total_duration_minutes"),
            "notes": log.get("notes"),
            "exercises": exercises,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"history session: {e}")
