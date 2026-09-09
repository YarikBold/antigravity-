import math

OLYMPIC_BAR = 20.0
PLATES = [25, 20, 15, 10, 5, 2.5, 1.25]

def round_to_plate(x: float) -> float:
    """Округление до шага 2.5 кг (спецификация: warm-up и рабочие веса)."""
    if x is None or x <= 0:
        return 0.0
    return round(round(x / 2.5) * 2.5, 2)

def warmup_sets(working_weight: float, equipment: str = "barbell") -> list[dict]:
    """3 разминки: 40%x8, 60%x5, 80%x2 if working_weight >=40 else []"""
    if working_weight is None or working_weight <= 0:
        return []
    if equipment not in ("barbell","dumbbell") or working_weight < 40:
        return []
    percents = [(0.4,8),(0.6,5),(0.8,2)]
    out=[]
    for p, reps in percents:
        w = round_to_plate(working_weight * p)
        if w < 20: w = 20
        out.append({"weight": w, "reps": reps, "percent": int(p*100)})
    return out

def epley_e1rm(weight: float, reps: int) -> float:
    if weight is None or weight <= 0:
        return 0.0
    if reps is None or reps <= 0: return round(weight,2)
    return round(weight * (1 + reps/30), 2)

def plate_breakdown(total_weight: float, bar: float = OLYMPIC_BAR) -> dict:
    """Visual plates per side from total (including bar)"""
    if total_weight <= bar:
        return {"bar": bar, "per_side": total_weight - bar if total_weight>bar else 0, "plates": []}
    per_side = (total_weight - bar)/2
    plates=[]
    rem = per_side
    for p in PLATES:
        while rem >= p - 1e-9:
            plates.append(p)
            rem = round(rem - p, 2)
    return {"bar": bar, "per_side": per_side, "plates": plates, "remainder": round(rem,2)}

def deload_check(readiness_history: list[float], volume_trend: list[float]) -> dict:
    """readiness 1-5, volume last 5 sessions"""
    flag=False
    reason=[]
    if len(readiness_history)>=5:
        avg = sum(readiness_history[-5:])/5
        if avg < 3.0:
            flag=True
            reason.append(f"avg readiness {avg:.2f} <3.0")
    if len(volume_trend)>=2 and volume_trend[-1] < volume_trend[-2] and (len(volume_trend)>=3 and volume_trend[-2] < volume_trend[-3] if len(volume_trend)>=3 else True):
        # 2 consecutive drops
        if len(volume_trend)>=2 and volume_trend[-1] < volume_trend[-2]:
            # check if 2 drops: need 3 points
            if len(volume_trend)>=3 and volume_trend[-2] < volume_trend[-3]:
                flag=True
                reason.append("volume drops 2 sessions")
    return {"deload": flag, "reason": "; ".join(reason) if reason else "ok", "suggestion": "Deload -40% sets" if flag else "continue"}

def rest_timer_for(rir: int, mechanics: str) -> int:
    """Dynamic rest per spec + checklist"""
    if mechanics == "isolation":
        return 60 if rir >= 2 else 90
    # compound
    return 180 if rir <= 1 else 120

def effective_weight(weight, reps, is_assisted: bool = False, bodyweight: float = 0.0) -> float:
    """Истинная нагрузка. Обычное: вес штанги. Гравитрон: max(0, bodyweight - assistance). Guards None/0 (checklist #3)."""
    try:
        w = float(weight or 0)
    except (TypeError, ValueError):
        return 0.0
    if is_assisted:
        try:
            bw = float(bodyweight or 0)
        except (TypeError, ValueError):
            bw = 0.0
        return round(max(0.0, bw - w), 2)
    return round(w, 2)

def assistance_delta(old_assistance, new_assistance) -> dict:
    """Инвертированный прогресс гравитрона: снижение противовеса = рост силы."""
    try:
        old = float(old_assistance or 0)
        new = float(new_assistance or 0)
    except (TypeError, ValueError):
        return {"delta": 0.0, "stronger": False, "message": ""}
    delta = round(old - new, 2)  # >0 значит стал сильнее
    if delta > 0:
        return {"delta": delta, "stronger": True,
                "message": f"Противовес снижен на {delta} кг! Ты тянешь больше своего веса!"}
    if delta < 0:
        return {"delta": delta, "stronger": False,
                "message": f"Противовес вырос на {abs(delta)} кг — лёгкая неделя, бывает."}
    return {"delta": 0.0, "stronger": False, "message": "Противовес без изменений."}

def effective_e1rm(weight, reps, is_assisted: bool = False, bodyweight: float = 0.0) -> float:
    """e1RM по Эпли строго от эффективной нагрузки."""
    try:
        r = int(reps or 0)
    except (TypeError, ValueError):
        r = 0
    return epley_e1rm(effective_weight(weight, reps, is_assisted, bodyweight), r)

def compare_exercise_to_last(exercise_id: str, name: str, cur_best: dict, prev_best: dict | None,
                             is_assisted: bool = False, bodyweight: float = 0.0) -> dict:
    """Сравнение лучшего сета упражнения с прошлой тренировкой. Guards None/0."""
    cur_w = float((cur_best or {}).get("weight") or 0)
    cur_r = int((cur_best or {}).get("reps") or 0)
    out = {"exercise_id": exercise_id, "name": name, "is_assisted": bool(is_assisted),
           "cur_weight": cur_w, "cur_reps": cur_r, "is_pr": False, "message": ""}
    if is_assisted:
        out["cur_effective"] = effective_weight(cur_w, cur_r, True, bodyweight)
        out["cur_e1rm"] = effective_e1rm(cur_w, cur_r, True, bodyweight)
        if not prev_best:
            out["message"] = "Первое измерение противовеса — база для прогресса."
            return out
        try:
            prev_w = float(prev_best.get("weight") or 0)
        except (TypeError, ValueError):
            prev_w = 0.0
        prog = assistance_delta(prev_w, cur_w)
        out["prev_assistance"] = prev_w
        out["assistance_delta"] = prog["delta"]
        out["stronger"] = prog["stronger"]
        out["message"] = prog["message"]
        if prog["stronger"]:
            out["is_pr"] = True
        return out
    out["cur_e1rm"] = epley_e1rm(cur_w, cur_r)
    if not prev_best:
        out["message"] = "Первое выполнение — точка отсчёта."
        return out
    try:
        prev_w = float(prev_best.get("weight") or 0)
        prev_r = int(prev_best.get("reps") or 0)
    except (TypeError, ValueError):
        prev_w, prev_r = 0.0, 0
    out["prev_weight"] = prev_w
    out["prev_reps"] = prev_r
    out["prev_e1rm"] = epley_e1rm(prev_w, prev_r)
    dw = round(cur_w - prev_w, 2)
    dr = cur_r - prev_r
    out["weight_delta"] = dw
    out["reps_delta"] = dr
    if dw > 0:
        out["is_pr"] = True
        out["message"] = f"Вес: {prev_w} кг → {cur_w} кг (+{dw} кг)"
    elif dw < 0:
        out["message"] = f"Вес: {prev_w} кг → {cur_w} кг ({dw} кг) — делоад/техника."
    elif dr > 0:
        out["is_pr"] = True
        out["message"] = f"Повторения: {prev_r} → {cur_r} (+{dr} повт. в лучшем сете)"
    else:
        out["message"] = f"Стабильно: {cur_w} кг × {cur_r}."
    return out

def mev_mav_status(sets_per_week: int, muscle: str) -> str:
    """MEV/MAV volume tracker color scale"""
    # simplified thresholds
    mav = {"chest":12,"back":14,"quads":12,"hamstrings":10,"glutes":12,"shoulders":12,"biceps":10,"triceps":10,"core":8}.get(muscle,10)
    mev = max(4, mav-6)
    if sets_per_week < mev: return "under"
    if sets_per_week <= mav: return "optimal"
    if sets_per_week <= mav+4: return "high"
    return "over"
