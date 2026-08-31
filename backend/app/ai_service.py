import json
import httpx
from .config import OPENROUTER_API_KEY, OPENROUTER_MODEL_PRIMARY, OPENROUTER_MODEL_FALLBACK

async def call_openrouter(prompt: str) -> dict:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY missing")
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://antigravity.app",
        "X-Title": "Antigravity",
    }
    for model in [OPENROUTER_MODEL_PRIMARY, OPENROUTER_MODEL_FALLBACK]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are a sports physiologist. Reply strictly in JSON, no markdown."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                })
                data = resp.json()
                if "error" in data:
                    raise RuntimeError(f"OpenRouter {model}: {data['error'].get('message') or data['error']}")
                if "choices" not in data or not data["choices"]:
                    raise RuntimeError(f"Bad response {model}: {str(data)[:400]}")
                content = data["choices"][0]["message"]["content"]
                # sanitize ```json fences per checklist
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                result = json.loads(content.strip())
                return result
        except Exception:
            continue
    raise RuntimeError("All OpenRouter models failed")

def fallback_substitutions(day_ex: list, all_ex: list, sore_muscles: list[str]) -> dict:
    sore_set = {m.lower().strip() for m in sore_muscles}
    if not sore_set:
        return {"substitutions": [], "general_advice": "Отдохни, лёгкая разминка и сон 7-8ч."}
    day_ids = {e["exercise_id"] for e in day_ex}
    cands = [e for e in all_ex if e["target_muscle"].lower() not in sore_set]
    if not cands:
        cands = [e for e in all_ex if e.get("movement_pattern") == "isolation"]
    subs = []
    for e in day_ex:
        mus = (e["exercises"]["target_muscle"] if e.get("exercises") else e.get("target_muscle","")).lower()
        if mus in sore_set:
            repl = next((c for c in cands if c["id"] not in day_ids), cands[0] if cands else None)
            if repl:
                subs.append({"original_exercise_id": e["exercise_id"], "replacement_exercise_id": repl["id"], "reason": f"{e['exercises']['name'] if e.get('exercises') else e['exercise_id']} нагружает {mus}, заменён на {repl['name']}"})
                day_ids.add(repl["id"])
    return {"substitutions": subs, "general_advice": "Снизь вес на 20-30%, увеличь отдых, не трогай болезненную мышцу напрямую. Боль ≥7 — skip."}
