from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..database import get_supabase
from ..ai_service import call_openrouter, fallback_substitutions

router = APIRouter(prefix="/api/readiness", tags=["readiness"])
legacy_router = APIRouter(prefix="/api", tags=["legacy"])

class ReadinessRequest(BaseModel):
    user_id: str
    plan_id: Optional[str] = None
    day_number: Optional[int] = None
    sore_muscles: List[str] = []
    pain_level: int = 1
    # new fields
    sleep_quality: Optional[int] = None
    stress_level: Optional[int] = None
    cns_fatigue: Optional[int] = None

class LegacyReadinessRequest(BaseModel):
    user_id: int
    plan_id: int
    day_number: int
    sore_muscles: List[str]
    pain_level: int

@router.post("/check")
async def check_readiness(req: ReadinessRequest):
    if req.pain_level < 7 and not req.sore_muscles:
        return {"status": "ok", "message": "Готов к тренировке!", "substitutions": [], "general_advice": ""}

    # also if pain <7 but some soreness -> still ok if not critical muscle for today
    if req.pain_level < 7:
        return {"status": "ok", "message": "Готов к тренировке! Лёгкая крепатура — снизь вес на 5-10% если нужно.", "substitutions": [], "general_advice": ""}

    sb = get_supabase()
    # fetch day exercises and all exercises (try UUID then legacy)
    day_ex = []
    all_ex = []
    try:
        if req.plan_id and req.day_number is not None:
            day_ex = sb.table("plan_exercises").select("*, exercises(*)").eq("plan_id", req.plan_id).eq("day_number", req.day_number).order("order_index").execute().data
        all_ex = sb.table("exercises").select("*").execute().data
        if not day_ex:
            # legacy fallback: plan_id int, day_number
            if req.plan_id and str(req.plan_id).isdigit() and req.day_number is not None:
                day_ex = sb.table("plan_exercises").select("*, exercises(*)").eq("plan_id", int(req.plan_id)).eq("day_number", req.day_number).execute().data
                if not all_ex:
                    all_ex = sb.table("exercises").select("*").execute().data
    except Exception as e:
        raise HTTPException(500, f"readiness fetch failed: {e}")

    if not day_ex:
        return {"status": "ok", "message": "Нет упражнений на сегодня", "substitutions": []}

    today_str = "\n".join([
        f"- ID {e['exercise_id']}: {e['exercises']['name']} (muscle:{e['exercises']['target_muscle']}, pattern:{e['exercises']['movement_pattern']}, cns:{e['exercises'].get('cns_load',3)}, stress:{','.join(e['exercises'].get('joint_stress') or [])})"
        for e in day_ex
    ])
    all_str = "\n".join([
        f"- ID {e['id']}: {e['name']} (muscle:{e['target_muscle']}, pattern:{e['movement_pattern']}, cns:{e.get('cns_load',3)}, stress:{','.join(e.get('joint_stress') or [])}, equip:{e.get('equipment','')})"
        for e in all_ex
    ])

    sore = ", ".join(req.sore_muscles) if req.sore_muscles else "none"
    prompt = (
        f"User DOMS pain {req.pain_level}/10 in: {sore}. Sleep {req.sleep_quality or '?'}/5, Stress {req.stress_level or '?'}/5, CNS {req.cns_fatigue or '?'}/5.\n"
        f"Today's exercises:\n{today_str}\n\nAll available:\n{all_str}\n\n"
        f"Task: find exercises that heavily load sore muscles/joints, suggest replacement with same movement_pattern but lower joint_stress and lower cns_load. "
        f"Only from All available list.\n"
        f'Reply STRICTLY JSON: {{"substitutions":[{{"original_exercise_id":"<uuid>","replacement_exercise_id":"<uuid>","reason":"<short>"}}],"general_advice":"<advice>"}}'
    )

    try:
        result = await call_openrouter(prompt)
        # ensure keys
        if "substitutions" not in result:
            result["substitutions"] = []
        return {"status": "modified", **result}
    except Exception as e:
        # fallback deterministic
        fb = fallback_substitutions(day_ex, all_ex, req.sore_muscles)
        if fb["substitutions"]:
            return {"status": "modified", "message": f"AI fallback: {e}", **fb}
        return {"status": "ok", "message": "Готов к тренировке — болезненная зона не участвует сегодня", "substitutions": [], "general_advice": fb["general_advice"]}

@legacy_router.post("/check_readiness")
async def legacy_check(req: LegacyReadinessRequest):
    mapped = ReadinessRequest(
        user_id=str(req.user_id),
        plan_id=str(req.plan_id),
        day_number=req.day_number,
        sore_muscles=req.sore_muscles,
        pain_level=req.pain_level
    )
    return await check_readiness(mapped)
