"""
Математика прогрессии — ТЗ:
 ИИ НИКОГДА не считает веса.
 Если подход в диапазоне цели с RIR >=1:
   target_weight = current_weight + 1.25 (изоляция/верх, cns<=2, isolation)
                   + 2.5  (база/низ, compound, cns>=3)
"""
from typing import Literal

def parse_target_reps(reps_target: str) -> int:
    """ '8-12' -> 12, '30-60с' -> 60, '8-10' -> 10 """
    import re
    nums = re.findall(r"\d+", reps_target)
    if not nums:
        return 10
    # берём верхнюю границу
    return int(nums[-1])

def increment_for_exercise(mechanics: str, cns_load: int, target_muscle: str) -> float:
    # изоляция/верх с низким CNS -> 1.25
    isolation_muscles = {"biceps","triceps","shoulders","core"}
    if mechanics == "isolation" or cns_load <= 2 or target_muscle in isolation_muscles:
        return 1.25
    return 2.5

def should_progress(reps: int, rir: int, target_reps: int, weight: float) -> bool:
    if weight <= 0:
        return False
    if rir < 1:
        return False
    if reps < target_reps:
        return False
    return True

def next_weight(current_weight: float, mechanics: str, cns_load: int, target_muscle: str) -> float:
    inc = increment_for_exercise(mechanics, cns_load, target_muscle)
    return round(current_weight + inc, 2)
