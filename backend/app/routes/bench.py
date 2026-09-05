from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..database import get_supabase
from ..bench_engine import (
    DEFAULT_BASE_1RM,
    apply_amrap_boost,
    base_from_pr,
    build_month_calendar,
)

router = APIRouter(prefix="/api/bench", tags=["bench"])


def _load_base_state(sb, user_id: Optional[str]) -> Optional[dict]:
    if not user_id:
        return None
    try:
        r = sb.table("bench_calendar_state").select("base_1rm, updated_at").eq("user_id", user_id).limit(1).execute()
        if r.data:
            return r.data[0]
    except Exception:
        pass
    return None


def _save_base_state(sb, user_id: str, new_base: float) -> bool:
    try:
        sb.table("bench_calendar_state").upsert(
            {"user_id": user_id, "base_1rm": new_base, "updated_at": date.today().isoformat()},
            on_conflict="user_id",
        ).execute()
        return True
    except Exception:
        return False


class LogDayRequest(BaseModel):
    user_id: str
    date: str                       # YYYY-MM-DD
    day_type: str = "heavy"         # heavy | volume
    planned_weight: Optional[float] = None
    actual_weight: Optional[float] = None
    reps: Optional[int] = None
    sets_done: Optional[int] = None
    amrap_reps: Optional[int] = None
    base_1rm: Optional[float] = None
    notes: Optional[str] = ""


class UpdateBaseRequest(BaseModel):
    user_id: str
    new_base_1rm: float
    reason: Optional[str] = ""


@router.get("/calendar")
async def bench_calendar(
    user_id: Optional[str] = None,
    base_1rm: Optional[float] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
):
    """Месячная сетка жим-календаря. Приоритет базы: сервер -> query -> 82.5 (75x3)."""
    today = date.today()
    y = year or today.year
    m = month or today.month
    if not (1 <= m <= 12):
        raise HTTPException(400, "month must be 1..12")

    persisted_base = None
    try:
        sb = get_supabase()
        state = _load_base_state(sb, user_id)
        if state:
            persisted_base = float(state["base_1rm"])
    except Exception:
        sb = None

    if persisted_base is not None:
        base = persisted_base
        source = "server"
    elif base_1rm and base_1rm > 0:
        base = float(base_1rm)
        source = "client"
    else:
        base = DEFAULT_BASE_1RM
        source = "default"

    logged_dates: list[str] = []
    if user_id and sb is not None:
        try:
            rows = (
                sb.table("bench_records")
                .select("date")
                .eq("user_id", user_id)
                .gte("date", date(y, m, 1).isoformat())
                .execute()
                .data
            )
            logged_dates = [str(r["date"]) for r in rows or []]
        except Exception:
            logged_dates = []

    return build_month_calendar(base, y, m, logged_dates) | {"base_source": source}


@router.post("/log-day")
async def bench_log_day(req: LogDayRequest):
    """Записать факт жимового дня. AMRAP >=3 повт. на 88% -> авто-буст базы +5 кг."""
    sb = None
    persisted = False
    try:
        sb = get_supabase()
    except Exception:
        pass

    state = _load_base_state(sb, req.user_id) if (sb and req.user_id) else None
    current_base = float(state["base_1rm"]) if state else (req.base_1rm or DEFAULT_BASE_1RM)

    if sb is not None:
        try:
            sb.table("bench_records").insert({
                "user_id": req.user_id,
                "date": req.date,
                "day_type": req.day_type,
                "planned_weight": req.planned_weight,
                "actual_weight": req.actual_weight,
                "reps": req.reps,
                "sets_done": req.sets_done,
                "amrap_reps": req.amrap_reps,
                "notes": req.notes or "",
            }).execute()
            persisted = True
        except Exception:
            persisted = False

    result = {
        "status": "ok",
        "persisted": persisted,
        "boosted": False,
        "new_base": current_base,
        "message": "Факт записан" if persisted else "Факт сохранён локально (таблица bench_records недоступна)",
    }

    if req.day_type == "heavy" and req.amrap_reps is not None:
        boost = apply_amrap_boost(current_base, req.actual_weight or req.planned_weight, req.amrap_reps)
        result["boosted"] = boost["boosted"]
        result["new_base"] = boost["new_base"]
        result["message"] = boost["reason"]
        if boost["boosted"]:
            result["base_persisted"] = _save_base_state(sb, req.user_id, boost["new_base"]) if sb else False
    return result


@router.post("/update-base")
async def bench_update_base(req: UpdateBaseRequest):
    """Ручное обновление базы 1ПМ (например, после нового рекорда)."""
    if req.new_base_1rm <= 0:
        raise HTTPException(400, "new_base_1rm must be positive")
    persisted = False
    try:
        sb = get_supabase()
        persisted = _save_base_state(sb, req.user_id, req.new_base_1rm)
    except Exception:
        persisted = False
    return {"status": "ok", "new_base_1rm": req.new_base_1rm, "persisted": persisted}


@router.get("/base/{user_id}")
async def bench_get_base(user_id: str):
    sb = None
    try:
        sb = get_supabase()
    except Exception:
        pass
    state = _load_base_state(sb, user_id) if sb else None
    if state:
        return {"base_1rm": float(state["base_1rm"]), "source": "server", "updated_at": state.get("updated_at")}
    return {"base_1rm": DEFAULT_BASE_1RM, "source": "default", "updated_at": None}


@router.post("/base-from-pr")
async def bench_base_from_pr(user_id: str, weight: float, reps: int):
    """Пересчитать базу из фактического рекорда (e1RM Эпли), например 75x3 -> 82.5."""
    base = base_from_pr(weight, reps)
    persisted = False
    try:
        sb = get_supabase()
        persisted = _save_base_state(sb, user_id, base)
    except Exception:
        persisted = False
    return {"base_1rm": base, "persisted": persisted}


@router.get("/probe")
async def bench_probe():
    """Диагностика: без обращения к БД — проверка математики цикла."""
    cal = build_month_calendar(DEFAULT_BASE_1RM, 2026, 9)
    heavy = [d for w in cal["weeks"] for d in w if d and d["type"] == "heavy"]
    return {
        "default_base": DEFAULT_BASE_1RM,
        "heavy_weeks": [{"day": h["day"], "percent": h["percent"], "weight": h["weight"], "amrap": h["amrap"]} for h in heavy],
        "boost_check": apply_amrap_boost(DEFAULT_BASE_1RM, 72.5, 4),
    }
