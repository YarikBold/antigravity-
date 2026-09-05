import math

OLYMPIC_BAR = 20.0
PLATES = [25, 20, 15, 10, 5, 2.5, 1.25]

def round_to_plate(x: float) -> float:
    return round(x * 2) / 2  # 2.5 kg step

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

def mev_mav_status(sets_per_week: int, muscle: str) -> str:
    """MEV/MAV volume tracker color scale"""
    # simplified thresholds
    mav = {"chest":12,"back":14,"quads":12,"hamstrings":10,"glutes":12,"shoulders":12,"biceps":10,"triceps":10,"core":8}.get(muscle,10)
    mev = max(4, mav-6)
    if sets_per_week < mev: return "under"
    if sets_per_week <= mav: return "optimal"
    if sets_per_week <= mav+4: return "high"
    return "over"
