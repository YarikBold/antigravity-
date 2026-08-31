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
    sleep_quality: Optional[int] = None
    stress_level: Optional[int] = None
    cns_fatigue: Optional[int] = None

class LegacyReadinessRequest(BaseModel):
    user_id: str
    plan_id: str
    day_number: int
    sore_muscles: List[str]
    pain_level: int

@router.post("/check")
async def check_readiness(req: ReadinessRequest):
    if req.pain_level < 7 and not req.sore_muscles:
        return {"status": "ok", "message": "Готов к тренировке!", "substitutions": [], "general_advice": ""}
    if req.pain_level < 7:
        return {"status": "ok", "message": "Готов к тренировке! Лёгкая крепатура — снизь вес на 5-10% если нужно.", "substitutions": [], "general_advice": ""}
    sb = get_supabase()
    day_ex=[]; all_ex=[]
    try:
        if req.plan_id and req.day_number is not None:
            day_ex = sb.table("plan_exercises").select("*, exercises(*)").eq("plan_id", req.plan_id).eq("day_number", req.day_number).order("order_index").execute().data
        all_ex = sb.table("exercises").select("*").execute().data
    except Exception as e:
        raise HTTPException(500, f"readiness fetch failed: {e}")
    if not day_ex:
        return {"status": "ok", "message": "Нет упражнений на сегодня", "substitutions": []}
    today_str = "\n".join([f"- ID {e['exercise_id']}: {e['exercises']['name']} (muscle:{e['exercises']['target_muscle']}, pattern:{e['exercises']['movement_pattern']}, cns:{e['exercises'].get('cns_load',3)})" for e in day_ex])
    all_str = "\n".join([f"- ID {e['id']}: {e['name']} (muscle:{e['target_muscle']}, pattern:{e['movement_pattern']}, cns:{e.get('cns_load',3)})" for e in all_ex])
    sore = ", ".join(req.sore_muscles) if req.sore_muscles else "none"
    prompt = (f"User DOMS pain {req.pain_level}/10 in: {sore}. Sleep {req.sleep_quality or '?'}/5, Stress {req.stress_level or '?'}/5, CNS {req.cns_fatigue or '?'}/5.\nToday:\n{today_str}\nAll:\n{all_str}\nTask: suggest replacement with same movement_pattern but lower joint_stress/cns. Reply STRICTLY JSON: {{\"substitutions\":[{{\"original_exercise_id\":\"<uuid>\",\"replacement_exercise_id\":\"<uuid>\",\"reason\":\"<short>\"}}],\"general_advice\":\"<advice>\"}}")
    try:
        result = await call_openrouter(prompt)
        if "substitutions" not in result: result["substitutions"]=[]
        return {"status": "modified", **result}
    except Exception as e:
        fb = fallback_substitutions(day_ex, all_ex, req.sore_muscles)
        if fb["substitutions"]:
            return {"status": "modified", "message": f"AI fallback: {e}", **fb}
        return {"status": "ok", "message": "Готов — болезненная зона не участвует сегодня", "substitutions": [], "general_advice": fb["general_advice"]}

@legacy_router.post("/check_readiness")
async def legacy_check(req: LegacyReadinessRequest):
    mapped = ReadinessRequest(user_id=str(req.user_id), plan_id=str(req.plan_id), day_number=req.day_number, sore_muscles=req.sore_muscles, pain_level=req.pain_level)
    return await check_readiness(mapped)
