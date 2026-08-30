import json
import httpx
from .config import OPENROUTER_API_KEY, OPENROUTER_MODEL_PRIMARY, OPENROUTER_MODEL_FALLBACK

SYSTEM = "You are a sports physiologist and biomechanics expert. Reply strictly in JSON, no markdown, no extra text."

def sanitize(content: str) -> str:
    content = content.strip()
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]
    return content.strip()

async def call_openrouter(prompt: str) -> dict:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY missing")
    last_err = None
    for model in [OPENROUTER_MODEL_PRIMARY, OPENROUTER_MODEL_FALLBACK]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://antigravity.app",
                        "X-Title": "Antigravity",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": SYSTEM},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.3,
                        "response_format": {"type": "json_object"},
                    },
                )
                data = resp.json()
                if "error" in data:
                    raise RuntimeError(f"{model} error: {data['error'].get('message') or data['error']}")
                if "choices" not in data or not data["choices"]:
                    raise RuntimeError(f"{model} bad response: {str(data)[:400]}")
                raw = data["choices"][0]["message"]["content"]
                cleaned = sanitize(raw)
                parsed = json.loads(cleaned)
                return parsed
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"AI unavailable: {last_err}")

def fallback_substitutions(day_ex: list, all_ex: list, sore_muscles: list[str]) -> dict:
    sore_set = {m.lower().strip() for m in sore_muscles}
    if not sore_set:
        return {"substitutions": [], "general_advice": "Сон 7-8ч, вода, лёгкая разминка."}
    day_ids = {e["exercise_id"] for e in day_ex}
    # кандидаты без стресса на больной сустав/мышцу
    cands = []
    for e in all_ex:
        if e["target_muscle"].lower() in sore_set:
            continue
        if any(j.lower() in sore_set for j in (e.get("joint_stress") or [])):
            continue
        # предпочитаем низкий cns_load
        cands.append(e)
    cands.sort(key=lambda x: x.get("cns_load", 3))
    if not cands:
        cands = [e for e in all_ex if e["target_muscle"].lower() not in sore_set]
    subs = []
    used = set(day_ids)
    for e in day_ex:
        # e = plan_exercise row with nested exercises
        mus = e["exercises"]["target_muscle"].lower()
        joints = [j.lower() for j in (e["exercises"].get("joint_stress") or [])]
        if mus in sore_set or any(j in sore_set for j in joints):
            repl = next((c for c in cands if c["id"] not in used), None)
            if repl:
                subs.append({
                    "original_exercise_id": e["exercise_id"],
                    "replacement_exercise_id": repl["id"],
                    "reason": f"{e['exercises']['name']} нагружает {mus} ({','.join(joints) or mus}), заменён на {repl['name']} ({repl['target_muscle']}, {repl['movement_pattern']}, cns {repl['cns_load']})"
                })
                used.add(repl["id"])
    return {
        "substitutions": subs,
        "general_advice": "Снизь вес на 20-30% для болезненных зон, увеличь отдых, избегай отказных подходов."
    }
