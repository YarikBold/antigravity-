"""
bench_engine.py — Жим-календарь [5]
Ускоренный цикл жима лёжа: база 1ПМ по Эпли, процентная сетка Пн (тяжёлый) / Чт (объёмный),
калькулятор блинов на сторону, AMRAP авто-буст базы (+5 кг при >=3 повторениях на 88%).
Стартовая база: рекорд 75x3 -> e1RM = 75*(1+3/30) = 82.5 кг. Цикл ведёт к 85-90 кг.
"""
from datetime import date, timedelta
from calendar import monthrange

from .math_engine import epley_e1rm, plate_breakdown

DEFAULT_BASE_1RM = 82.5
TARGET_BASE_MIN = 85.0
TARGET_BASE_MAX = 90.0
AMRAP_BOOST_KG = 5.0
AMRAP_MIN_REPS = 3

# Процентная сетка от 1ПМ: неделя 1..4+ (5-я неделя повторяет 4-ю)
HEAVY_PERCENTS = [0.75, 0.82, 0.88, 0.85]   # Пн: 3-5 повторений
VOLUME_PERCENTS = [0.65, 0.68, 0.70, 0.72]  # Чт: 6-8 повторений

HEAVY_SETS = 4
HEAVY_REPS = 4          # середина диапазона 3-5
VOLUME_SETS = 4
VOLUME_REPS = 7         # середина диапазона 6-8

DOW_NAMES = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
# ОФП-карточки для не-жимовых дней
OFP_BY_DOW = {1: "Спина", 2: "Ноги", 4: "Плечи и руки"}  # Вт, Ср, Пт


def round_to_2_5(x: float) -> float:
    if x is None:
        return 0.0
    return round(round(x / 2.5) * 2.5, 2)


def base_from_pr(weight: float, reps: int) -> float:
    """Расчётная база 1ПМ по Эпли (75x3 -> 82.5)."""
    return float(epley_e1rm(weight, reps))


def week_percent(kind: str, week_num: int) -> float:
    percents = HEAVY_PERCENTS if kind == "heavy" else VOLUME_PERCENTS
    idx = min(max(week_num, 1), len(percents)) - 1
    return percents[idx]


def build_day(base_1rm: float, d: date, week_num: int, amrap_week: int = 3) -> dict:
    """Собирает карточку одного дня календаря (Пн-Пт)."""
    dow = d.weekday()  # 0=Пн .. 6=Вс
    day = {
        "date": d.isoformat(),
        "day": d.day,
        "dow": DOW_NAMES[dow],
        "week_num": week_num,
        "type": "info",
        "title": "",
        "percent": None,
        "percent_delta": None,
        "weight": None,
        "sets": None,
        "reps": None,
        "plates": [],
        "amrap": False,
        "logged": False,
    }

    if dow == 0:  # Понедельник — тяжёлый жим
        percent = week_percent("heavy", week_num)
        weight = round_to_2_5(base_1rm * percent)
        day.update({
            "type": "heavy",
            "title": "Тяжелый жим",
            "percent": int(round(percent * 100)),
            "weight": weight,
            "sets": HEAVY_SETS,
            "reps": HEAVY_REPS,
            "amrap": week_num == amrap_week,
            "plates": plate_breakdown(weight).get("plates", []),
        })
    elif dow == 3:  # Четверг — скоростной / объёмный
        percent = week_percent("volume", week_num)
        weight = round_to_2_5(base_1rm * percent)
        day.update({
            "type": "volume",
            "title": "Скоростной жим",
            "percent": int(round(percent * 100)),
            "weight": weight,
            "sets": VOLUME_SETS,
            "reps": VOLUME_REPS,
            "plates": plate_breakdown(weight).get("plates", []),
        })
    elif dow in OFP_BY_DOW:
        day["title"] = f"ОФП: {OFP_BY_DOW[dow]}"
    return day


def build_month_calendar(base_1rm: float, year: int, month: int, logged_dates: list[str] | None = None) -> dict:
    """Интерактивный календарь Пн-Пт с 1-го числа месяца.

    Возвращает сетку недель: пустые ячейки до 1-го числа, Сб/Вс исключены.
    AMRAP-день — тяжёлый Понедельник 3-й недели.
    """
    base_1rm = float(base_1rm or DEFAULT_BASE_1RM)
    logged = set(logged_dates or [])
    days_in_month = monthrange(year, month)[1]
    first = date(year, month, 1)

    weeks: list[list[dict | None]] = []
    current_week: list[dict | None] = [None] * first.weekday()  # паддинг до Пн

    for day_num in range(1, days_in_month + 1):
        d = date(year, month, day_num)
        week_num = (day_num - 1) // 7 + 1
        card = build_day(base_1rm, d, week_num)
        card["logged"] = card["date"] in logged
        current_week.append(card)
        if d.weekday() == 4:  # Пт закрывает неделю (Сб/Вс не рендерим)
            weeks.append(current_week)
            current_week = []
    if current_week:
        current_week += [None] * (5 - len(current_week))
        weeks.append(current_week)

    heavy_week1 = int(round(HEAVY_PERCENTS[0] * 100))
    for week in weeks:
        for cell in week:
            if cell and cell.get("percent") is not None:
                cell["percent_delta"] = cell["percent"] - heavy_week1

    amrap_day = None
    for week in weeks:
        for cell in week:
            if cell and cell.get("amrap"):
                amrap_day = cell["date"]
                break

    return {
        "base_1rm": base_1rm,
        "target": {"min": TARGET_BASE_MIN, "max": TARGET_BASE_MAX},
        "amrap": {
            "week": 3,
            "min_reps": AMRAP_MIN_REPS,
            "boost_kg": AMRAP_BOOST_KG,
            "date": amrap_day,
            "rule": f"AMRAP в последнем сете на {int(round(HEAVY_PERCENTS[2]*100))}% 1ПМ: >= {AMRAP_MIN_REPS} повторений -> база +{AMRAP_BOOST_KG} кг",
        },
        "month": {"year": year, "month": month,
                  "label": f"{year}-{month:02d}"},
        "weeks": weeks,
    }


def apply_amrap_boost(base_1rm: float, amrap_weight: float, amrap_reps: int) -> dict:
    """AMRAP авто-буст: >=3 повторений с весом 88% 1ПМ -> база +5 кг."""
    base_1rm = float(base_1rm or DEFAULT_BASE_1RM)
    threshold = round_to_2_5(base_1rm * HEAVY_PERCENTS[2])
    if amrap_reps is None or amrap_reps < AMRAP_MIN_REPS:
        return {"boosted": False, "new_base": base_1rm,
                "reason": f"AMRAP {amrap_reps or 0} повт. < {AMRAP_MIN_REPS} — база без изменений"}
    # Буст засчитываем при весе >= 85% от порога 88% (допуск округления блинов)
    if amrap_weight is None or amrap_weight + 1e-9 < threshold - 2.5:
        return {"boosted": False, "new_base": base_1rm,
                "reason": f"Вес {amrap_weight}кг ниже рабочего ({threshold}кг) — база без изменений"}
    new_base = round_to_2_5(base_1rm + AMRAP_BOOST_KG)
    return {"boosted": True, "new_base": new_base,
            "reason": f"AMRAP {amrap_reps} повт. × {amrap_weight}кг (>=88%) — база 1ПМ: {base_1rm} -> {new_base} кг"}
