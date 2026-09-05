def parse_target_reps(target: str) -> int:
    """'8-12' -> 12, '30-60с' -> 60"""
    if not target: return 10
    import re
    nums = re.findall(r"\d+", str(target))
    if not nums: return 10
    return int(nums[-1])

def should_progress(reps: int, rir: int, target_reps: int, weight: float) -> bool:
    if weight is None or reps is None or rir is None:
        return False
    return weight>0 and rir>=1 and reps >= target_reps

def next_weight(weight: float, mechanics: str, cns_load: int, target_muscle: str) -> float:
    if weight is None or weight <= 0:
        return weight or 0
    # isolation +1.25 else +2.5 ; heavy compounds +2.5..5
    is_iso = mechanics == "isolation" or (cns_load or 3) <= 2
    inc = 1.25 if is_iso else 2.5
    # extra for high cns compound with RIR>=3 will be handled in suggest
    return round(weight + inc, 2)

def suggest_next_set(rir: int, reps: int, target_reps_str: str, weight: float, mechanics: str, cns_load: int, target_muscle: str) -> dict:
    """RIR-autoregulation [10] per spec"""
    if weight is None or weight <= 0:
        return {"action": "hold", "next_weight": 0, "next_reps": 0, "badge": "кардио / conditioning — без прогрессии веса"}
    tr = parse_target_reps(target_reps_str)
    is_iso = mechanics == "isolation" or (cns_load or 3) <= 2
    if rir >= 3:
        inc = 2.5 if is_iso else 5.0
        # cap isolation to 2.5
        if is_iso: inc = 2.5
        return {"action": "increase", "next_weight": round(weight+inc,2), "next_reps": tr, "badge": f"+{inc}кг — легко (RIR {rir})"}
    if rir == 2 and reps >= tr:
        inc = 1.25 if is_iso else 2.5
        return {"action": "increase", "next_weight": round(weight+inc,2), "next_reps": tr, "badge": f"+{inc}кг — цель выполнена"}
    if rir == 1:
        return {"action": "hold", "next_weight": weight, "next_reps": reps, "badge": "фиксируй — идеальная нагрузка"}
    # RIR 0 or reps under target
    dec = round(weight*0.07,2)  # 7%
    # round to 1.25
    dec = max(1.25, round(dec*4)/4)
    return {"action": "decrease", "next_weight": max(0, round(weight-dec,2)), "next_reps": tr, "badge": f"-{dec}кг — техника, RIR {rir}"}
