"""
generate_exercise_docs.py — генерирует database/exercise_analysis.json и docs/exercise_guide.md
из состава планов (тот же набор данных, что в database/seed.sql и backend/scripts/apply_plan_update.py).
Для каждого упражнения плана подбирает "лучший метод" (suggested_method из плана) и 3 альтернативы
по тому же алгоритму, что использует /api/workouts/swap-exercise (movement_pattern -> muscle fallback).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

EXERCISES = {
    "Присед со штангой": dict(target_muscle="quads", movement_pattern="squat", equipment="barbell", mechanics="compound", joint_stress=["knee","lumbar"], cns_load=5),
    "Жим штанги лёжа": dict(target_muscle="chest", movement_pattern="horizontal_push", equipment="barbell", mechanics="compound", joint_stress=["shoulder","elbow"], cns_load=4),
    "Тяга штанги в наклоне": dict(target_muscle="back", movement_pattern="horizontal_pull", equipment="barbell", mechanics="compound", joint_stress=["lumbar","elbow"], cns_load=4),
    "Румынская тяга": dict(target_muscle="hamstrings", movement_pattern="hinge", equipment="barbell", mechanics="compound", joint_stress=["lumbar","hamstring"], cns_load=4),
    "Жим гантелей на наклонной": dict(target_muscle="chest", movement_pattern="horizontal_push", equipment="dumbbell", mechanics="compound", joint_stress=["shoulder"], cns_load=3),
    "Тяга верхнего блока": dict(target_muscle="back", movement_pattern="vertical_pull", equipment="cable", mechanics="compound", joint_stress=["elbow","shoulder"], cns_load=3),
    "Жим штанги стоя": dict(target_muscle="shoulders", movement_pattern="vertical_push", equipment="barbell", mechanics="compound", joint_stress=["shoulder","lumbar"], cns_load=4),
    "Ягодичный мостик": dict(target_muscle="glutes", movement_pattern="hinge", equipment="barbell", mechanics="compound", joint_stress=[], cns_load=2),
    "Болгарские сплит-приседы": dict(target_muscle="glutes", movement_pattern="lunge", equipment="dumbbell", mechanics="compound", joint_stress=["knee"], cns_load=3),
    "Жим ногами": dict(target_muscle="quads", movement_pattern="squat", equipment="machine", mechanics="compound", joint_stress=["knee"], cns_load=3),
    "Сведение рук в кроссовере": dict(target_muscle="chest", movement_pattern="isolation", equipment="cable", mechanics="isolation", joint_stress=["shoulder"], cns_load=1),
    "Махи гантелей в стороны": dict(target_muscle="shoulders", movement_pattern="isolation", equipment="dumbbell", mechanics="isolation", joint_stress=["shoulder"], cns_load=1),
    "Сгибание рук с гантелями": dict(target_muscle="biceps", movement_pattern="isolation", equipment="dumbbell", mechanics="isolation", joint_stress=["elbow"], cns_load=1),
    "Разгибание на трицепс": dict(target_muscle="triceps", movement_pattern="isolation", equipment="cable", mechanics="isolation", joint_stress=["elbow"], cns_load=1),
    "Сгибание ног лёжа": dict(target_muscle="hamstrings", movement_pattern="isolation", equipment="machine", mechanics="isolation", joint_stress=["knee"], cns_load=1),
    "Негативные подтягивания": dict(target_muscle="back", movement_pattern="vertical_pull", equipment="bodyweight", mechanics="compound", joint_stress=["elbow","shoulder"], cns_load=3),
    "Австралийские подтягивания": dict(target_muscle="back", movement_pattern="horizontal_pull", equipment="bodyweight", mechanics="compound", joint_stress=["shoulder"], cns_load=2),
    "Подтягивания с эспандером": dict(target_muscle="back", movement_pattern="vertical_pull", equipment="band", mechanics="compound", joint_stress=["shoulder"], cns_load=2),
    "Планка": dict(target_muscle="core", movement_pattern="core", equipment="bodyweight", mechanics="isolation", joint_stress=[], cns_load=1),
    "Скручивания на пресс": dict(target_muscle="core", movement_pattern="core", equipment="bodyweight", mechanics="isolation", joint_stress=["lumbar"], cns_load=1),
    "Отжимания": dict(target_muscle="chest", movement_pattern="horizontal_push", equipment="bodyweight", mechanics="compound", joint_stress=["shoulder","elbow"], cns_load=2),
    "Гиперэкстензия": dict(target_muscle="hamstrings", movement_pattern="hinge", equipment="bodyweight", mechanics="isolation", joint_stress=["lumbar"], cns_load=2),
    "Подтягивания в гравитроне": dict(target_muscle="back", movement_pattern="vertical_pull", equipment="machine", mechanics="compound", joint_stress=["elbow","shoulder"], cns_load=3),
    "Жим сидя в тренажёре": dict(target_muscle="shoulders", movement_pattern="vertical_push", equipment="machine", mechanics="compound", joint_stress=["shoulder","elbow"], cns_load=3),
    "Жим от груди в хаммере": dict(target_muscle="chest", movement_pattern="horizontal_push", equipment="machine", mechanics="compound", joint_stress=["shoulder","elbow"], cns_load=3),
    "Тяга Т-грифа с упором в грудь": dict(target_muscle="back", movement_pattern="horizontal_pull", equipment="machine", mechanics="compound", joint_stress=["elbow"], cns_load=3),
    "Румынская тяга с гантелями": dict(target_muscle="hamstrings", movement_pattern="hinge", equipment="dumbbell", mechanics="compound", joint_stress=["lumbar","hamstring"], cns_load=4),
    "Выпады со штангой в Смите": dict(target_muscle="glutes", movement_pattern="lunge", equipment="barbell", mechanics="compound", joint_stress=["knee"], cns_load=3),
    "Тяга каната к лицу (Face Pull)": dict(target_muscle="shoulders", movement_pattern="isolation", equipment="cable", mechanics="isolation", joint_stress=["shoulder"], cns_load=1),
    "Подъём штанги на бицепс": dict(target_muscle="biceps", movement_pattern="isolation", equipment="barbell", mechanics="isolation", joint_stress=["elbow"], cns_load=1),
    "Подъём гантелей на бицепс на наклонной": dict(target_muscle="biceps", movement_pattern="isolation", equipment="dumbbell", mechanics="isolation", joint_stress=["elbow"], cns_load=1),
    "Молотковые сгибания стоя": dict(target_muscle="biceps", movement_pattern="isolation", equipment="dumbbell", mechanics="isolation", joint_stress=["elbow"], cns_load=1),
    "Жим гантели из-за головы": dict(target_muscle="triceps", movement_pattern="isolation", equipment="dumbbell", mechanics="isolation", joint_stress=["elbow","shoulder"], cns_load=1),
    "Разведение ног сидя": dict(target_muscle="glutes", movement_pattern="isolation", equipment="machine", mechanics="isolation", joint_stress=[], cns_load=1),
    "Отведение ноги с манжетой на нижнем блоке": dict(target_muscle="glutes", movement_pattern="isolation", equipment="cable", mechanics="isolation", joint_stress=[], cns_load=1),
    "Разгибания ног сидя": dict(target_muscle="quads", movement_pattern="isolation", equipment="machine", mechanics="isolation", joint_stress=["knee"], cns_load=1),
    "Сведения в тренажёре «Бабочка»": dict(target_muscle="chest", movement_pattern="isolation", equipment="machine", mechanics="isolation", joint_stress=["shoulder"], cns_load=1),
}

PLAN_333 = "33333333-3333-3333-3333-333333333333"
PLAN_444 = "44444444-4444-4444-4444-444444444444"

# (day_number, exercise_name, best_method)
PLAN_333_DAYS = {
    1: ["Присед со штангой","Жим штанги лёжа","Подтягивания в гравитроне","Жим сидя в тренажёре","Подъём штанги на бицепс","Жим гантели из-за головы","Гиперэкстензия"],
    2: ["Румынская тяга с гантелями","Жим от груди в хаммере","Тяга Т-грифа с упором в грудь","Тяга каната к лицу (Face Pull)","Подъём гантелей на бицепс на наклонной","Разгибание на трицепс","Молотковые сгибания стоя"],
}
PLAN_333_METHODS = {
    "Присед со штангой": "pyramid", "Жим штанги лёжа": "normal", "Подтягивания в гравитроне": "rest_pause",
    "Жим сидя в тренажёре": "normal", "Подъём штанги на бицепс": "drop_set", "Жим гантели из-за головы": "drop_set",
    "Гиперэкстензия": "normal", "Румынская тяга с гантелями": "pyramid", "Жим от груди в хаммере": "normal",
    "Тяга Т-грифа с упором в грудь": "normal", "Тяга каната к лицу (Face Pull)": "drop_set",
    "Подъём гантелей на бицепс на наклонной": "drop_set", "Разгибание на трицепс": "drop_set", "Молотковые сгибания стоя": "drop_set",
}
PLAN_444_DAYS = {
    1: ["Ягодичный мостик","Болгарские сплит-приседы","Жим ногами","Разведение ног сидя","Гиперэкстензия","Жим от груди в хаммере"],
    2: ["Жим штанги лёжа","Жим гантелей на наклонной","Сведения в тренажёре «Бабочка»","Подтягивания в гравитроне","Жим сидя в тренажёре","Тяга каната к лицу (Face Pull)"],
    3: ["Румынская тяга","Сгибание ног лёжа","Выпады со штангой в Смите","Отведение ноги с манжетой на нижнем блоке","Разгибания ног сидя","Скручивания на пресс"],
}
PLAN_444_METHODS = {
    "Ягодичный мостик": "normal", "Болгарские сплит-приседы": "normal", "Жим ногами": "normal",
    "Разведение ног сидя": "drop_set", "Гиперэкстензия": "normal", "Жим от груди в хаммере": "drop_set",
    "Жим штанги лёжа": "normal", "Жим гантелей на наклонной": "normal", "Сведения в тренажёре «Бабочка»": "drop_set",
    "Подтягивания в гравитроне": "rest_pause", "Жим сидя в тренажёре": "normal", "Тяга каната к лицу (Face Pull)": "drop_set",
    "Румынская тяга": "pyramid", "Сгибание ног лёжа": "drop_set", "Выпады со штангой в Смите": "pyramid",
    "Отведение ноги с манжетой на нижнем блоке": "drop_set", "Разгибания ног сидя": "drop_set", "Скручивания на пресс": "amrap",
}

METHOD_WHY = {
    "pyramid": "тяжёлый компаунд, высокая CNS-нагрузка — пирамида (нарастающий вес, снижающиеся повторы) безопаснее работы в отказ",
    "rest_pause": "среднетяжёлый компаунд/блочное упражнение — rest-pause (пауза 10-15с) добивает 2-3 повтора без потери техники",
    "drop_set": "изоляция или лёгкий тренажёр — дроп-сет (снижение веса на 20-30% без отдыха) добивает мышцу в конце",
    "amrap": "статика/пресс — AMRAP (максимум повторов/времени в подходе) удобнее фиксированной цифры",
    "normal": "стандартный компаунд средней тяжести — обычные подходы с прогрессией веса по RIR",
}


def score(cur, cand):
    s = 0
    if cand["target_muscle"] == cur["target_muscle"]: s -= 10
    if cand["mechanics"] == cur["mechanics"]: s -= 5
    if cand["equipment"] != cur["equipment"]: s -= 3
    s += cand["cns_load"]
    s += len(cand["joint_stress"])
    return s


def pick_alternatives(name, k=3):
    cur = EXERCISES[name]
    same_pattern = [n for n, a in EXERCISES.items() if n != name and a["movement_pattern"] == cur["movement_pattern"]]
    same_muscle = [n for n, a in EXERCISES.items() if n != name and a["target_muscle"] == cur["target_muscle"] and n not in same_pattern]
    pool = same_pattern + same_muscle
    pool.sort(key=lambda n: score(cur, EXERCISES[n]))
    out = []
    for n in pool:
        if len(out) >= k: break
        a = EXERCISES[n]
        reason = f"{a['movement_pattern']}/{a['equipment']}"
        if a["target_muscle"] == cur["target_muscle"] and a["movement_pattern"] != cur["movement_pattern"]:
            reason += " — та же мышца, другой паттерн"
        elif a["equipment"] != cur["equipment"]:
            reason += " — тот же паттерн, свободна другая станция"
        else:
            reason += " — прямая замена"
        out.append(dict(name=n, target_muscle=a["target_muscle"], movement_pattern=a["movement_pattern"], equipment=a["equipment"], cns_load=a["cns_load"], reason=reason))
    return out


def build_exercise_entry(name, method):
    a = EXERCISES[name]
    return dict(
        name=name,
        attributes=dict(muscle=a["target_muscle"], pattern=a["movement_pattern"], equip=a["equipment"], mech=a["mechanics"], cns=a["cns_load"], stress=a["joint_stress"]),
        best_method=method,
        method_reason=METHOD_WHY[method],
        alternatives=pick_alternatives(name),
    )


def build_plan(plan_id, name, days, methods):
    return dict(id=plan_id, name=name, days=[
        dict(day_number=d, exercises=[build_exercise_entry(n, methods[n]) for n in names])
        for d, names in days.items()
    ])


def main():
    data = dict(plans=[
        build_plan(PLAN_333, "Full Body A/B — Reboot", PLAN_333_DAYS, PLAN_333_METHODS),
        build_plan(PLAN_444, "Низ/Верх/Низ — Shape", PLAN_444_DAYS, PLAN_444_METHODS),
    ])
    out_json = ROOT / "database" / "exercise_analysis.json"
    out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_json}")

    day_titles_333 = {1: "День А", 2: "День Б"}
    day_titles_444 = {1: "День 1 (Низ)", 2: "День 2 (Верх)", 3: "День 3 (Низ)"}

    lines = ["# Antigravity — Разбор упражнений: альтернативы и продвинутые методы", ""]
    for plan in data["plans"]:
        titles = day_titles_333 if plan["id"] == PLAN_333 else day_titles_444
        lines.append(f"## {plan['name']} `{plan['id']}`")
        for day in plan["days"]:
            lines.append(f"### {titles[day['day_number']]}")
            lines.append("| Упражнение | Лучший метод | Почему | Альтернатива 1 | Альтернатива 2 | Альтернатива 3 |")
            lines.append("|---|---|---|---|---|---|")
            for ex in day["exercises"]:
                alt_cells = []
                for alt in ex["alternatives"]:
                    alt_cells.append(f"{alt['name']} ({alt['equipment']}, {alt['movement_pattern']})<br><sub>{alt['reason']}</sub>")
                while len(alt_cells) < 3:
                    alt_cells.append("—")
                name_cell = f"**{ex['name']}**<br><sub>{ex['attributes']['muscle']}/{ex['attributes']['pattern']}</sub>"
                lines.append(f"| {name_cell} | `{ex['best_method']}` | {ex['method_reason']} | " + " | ".join(alt_cells) + " |")
            lines.append("")
    out_md = ROOT / "docs" / "exercise_guide.md"
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()
