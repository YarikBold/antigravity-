"""
apply_plan_update.py — применяет обновление планов тренировок (database/seed.sql)
напрямую в Supabase через REST API (supabase-py), без прямого доступа к Postgres.

Использование:
  python backend/scripts/apply_plan_update.py --dry-run   # только показать, что будет сделано
  python backend/scripts/apply_plan_update.py              # применить изменения

Требует SUPABASE_URL / SUPABASE_KEY в .env (ищет в корне репозитория и в backend/).
"""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / "backend" / ".env")

from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# --- Данные упражнений (полный набор — существующие + новые из документа) ---
EXERCISES = [
    dict(name="Присед со штангой", target_muscle="quads", synergists=["glutes","hamstrings"], movement_pattern="squat", equipment="barbell", mechanics="compound", joint_stress=["knee","lumbar"], cns_load=5),
    dict(name="Жим штанги лёжа", target_muscle="chest", synergists=["triceps","shoulders"], movement_pattern="horizontal_push", equipment="barbell", mechanics="compound", joint_stress=["shoulder","elbow"], cns_load=4),
    dict(name="Тяга штанги в наклоне", target_muscle="back", synergists=["biceps","rear_delts"], movement_pattern="horizontal_pull", equipment="barbell", mechanics="compound", joint_stress=["lumbar","elbow"], cns_load=4),
    dict(name="Румынская тяга", target_muscle="hamstrings", synergists=["glutes","erector"], movement_pattern="hinge", equipment="barbell", mechanics="compound", joint_stress=["lumbar","hamstring"], cns_load=4),
    dict(name="Жим гантелей на наклонной", target_muscle="chest", synergists=["triceps","shoulders"], movement_pattern="horizontal_push", equipment="dumbbell", mechanics="compound", joint_stress=["shoulder"], cns_load=3),
    dict(name="Тяга верхнего блока", target_muscle="back", synergists=["biceps"], movement_pattern="vertical_pull", equipment="cable", mechanics="compound", joint_stress=["elbow","shoulder"], cns_load=3),
    dict(name="Жим штанги стоя", target_muscle="shoulders", synergists=["triceps","core"], movement_pattern="vertical_push", equipment="barbell", mechanics="compound", joint_stress=["shoulder","lumbar"], cns_load=4),
    dict(name="Ягодичный мостик", target_muscle="glutes", synergists=["hamstrings"], movement_pattern="hinge", equipment="barbell", mechanics="compound", joint_stress=[], cns_load=2),
    dict(name="Болгарские сплит-приседы", target_muscle="glutes", synergists=["quads","hamstrings"], movement_pattern="lunge", equipment="dumbbell", mechanics="compound", joint_stress=["knee"], cns_load=3),
    dict(name="Жим ногами", target_muscle="quads", synergists=["glutes"], movement_pattern="squat", equipment="machine", mechanics="compound", joint_stress=["knee"], cns_load=3),
    dict(name="Сведение рук в кроссовере", target_muscle="chest", synergists=[], movement_pattern="isolation", equipment="cable", mechanics="isolation", joint_stress=["shoulder"], cns_load=1),
    dict(name="Махи гантелей в стороны", target_muscle="shoulders", synergists=[], movement_pattern="isolation", equipment="dumbbell", mechanics="isolation", joint_stress=["shoulder"], cns_load=1),
    dict(name="Сгибание рук с гантелями", target_muscle="biceps", synergists=[], movement_pattern="isolation", equipment="dumbbell", mechanics="isolation", joint_stress=["elbow"], cns_load=1),
    dict(name="Разгибание на трицепс", target_muscle="triceps", synergists=[], movement_pattern="isolation", equipment="cable", mechanics="isolation", joint_stress=["elbow"], cns_load=1),
    dict(name="Сгибание ног лёжа", target_muscle="hamstrings", synergists=[], movement_pattern="isolation", equipment="machine", mechanics="isolation", joint_stress=["knee"], cns_load=1),
    dict(name="Негативные подтягивания", target_muscle="back", synergists=["biceps"], movement_pattern="vertical_pull", equipment="bodyweight", mechanics="compound", joint_stress=["elbow","shoulder"], cns_load=3),
    dict(name="Австралийские подтягивания", target_muscle="back", synergists=["biceps"], movement_pattern="horizontal_pull", equipment="bodyweight", mechanics="compound", joint_stress=["shoulder"], cns_load=2),
    dict(name="Подтягивания с эспандером", target_muscle="back", synergists=["biceps"], movement_pattern="vertical_pull", equipment="band", mechanics="compound", joint_stress=["shoulder"], cns_load=2),
    dict(name="Планка", target_muscle="core", synergists=[], movement_pattern="core", equipment="bodyweight", mechanics="isolation", joint_stress=[], cns_load=1),
    dict(name="Скручивания на пресс", target_muscle="core", synergists=["hip_flexors"], movement_pattern="core", equipment="bodyweight", mechanics="isolation", joint_stress=["lumbar"], cns_load=1),
    dict(name="Отжимания", target_muscle="chest", synergists=["triceps","shoulders"], movement_pattern="horizontal_push", equipment="bodyweight", mechanics="compound", joint_stress=["shoulder","elbow"], cns_load=2),
    dict(name="Гиперэкстензия", target_muscle="hamstrings", synergists=["glutes","erector"], movement_pattern="hinge", equipment="bodyweight", mechanics="isolation", joint_stress=["lumbar"], cns_load=2),
    # Новые упражнения (документ «план тренировок»)
    dict(name="Подтягивания в гравитроне", target_muscle="back", synergists=["biceps"], movement_pattern="vertical_pull", equipment="machine", mechanics="compound", joint_stress=["elbow","shoulder"], cns_load=3),
    dict(name="Жим сидя в тренажёре", target_muscle="shoulders", synergists=["triceps"], movement_pattern="vertical_push", equipment="machine", mechanics="compound", joint_stress=["shoulder","elbow"], cns_load=3),
    dict(name="Жим от груди в хаммере", target_muscle="chest", synergists=["triceps","shoulders"], movement_pattern="horizontal_push", equipment="machine", mechanics="compound", joint_stress=["shoulder","elbow"], cns_load=3),
    dict(name="Тяга Т-грифа с упором в грудь", target_muscle="back", synergists=["biceps","rear_delts"], movement_pattern="horizontal_pull", equipment="machine", mechanics="compound", joint_stress=["elbow"], cns_load=3),
    dict(name="Румынская тяга с гантелями", target_muscle="hamstrings", synergists=["glutes","erector"], movement_pattern="hinge", equipment="dumbbell", mechanics="compound", joint_stress=["lumbar","hamstring"], cns_load=4),
    dict(name="Выпады со штангой в Смите", target_muscle="glutes", synergists=["quads","hamstrings"], movement_pattern="lunge", equipment="barbell", mechanics="compound", joint_stress=["knee"], cns_load=3),
    dict(name="Тяга каната к лицу (Face Pull)", target_muscle="shoulders", synergists=["rear_delts"], movement_pattern="isolation", equipment="cable", mechanics="isolation", joint_stress=["shoulder"], cns_load=1),
    dict(name="Подъём штанги на бицепс", target_muscle="biceps", synergists=[], movement_pattern="isolation", equipment="barbell", mechanics="isolation", joint_stress=["elbow"], cns_load=1),
    dict(name="Подъём гантелей на бицепс на наклонной", target_muscle="biceps", synergists=[], movement_pattern="isolation", equipment="dumbbell", mechanics="isolation", joint_stress=["elbow"], cns_load=1),
    dict(name="Молотковые сгибания стоя", target_muscle="biceps", synergists=["forearms"], movement_pattern="isolation", equipment="dumbbell", mechanics="isolation", joint_stress=["elbow"], cns_load=1),
    dict(name="Жим гантели из-за головы", target_muscle="triceps", synergists=[], movement_pattern="isolation", equipment="dumbbell", mechanics="isolation", joint_stress=["elbow","shoulder"], cns_load=1),
    dict(name="Разведение ног сидя", target_muscle="glutes", synergists=[], movement_pattern="isolation", equipment="machine", mechanics="isolation", joint_stress=[], cns_load=1),
    dict(name="Отведение ноги с манжетой на нижнем блоке", target_muscle="glutes", synergists=[], movement_pattern="isolation", equipment="cable", mechanics="isolation", joint_stress=[], cns_load=1),
    dict(name="Разгибания ног сидя", target_muscle="quads", synergists=[], movement_pattern="isolation", equipment="machine", mechanics="isolation", joint_stress=["knee"], cns_load=1),
    dict(name="Сведения в тренажёре «Бабочка»", target_muscle="chest", synergists=[], movement_pattern="isolation", equipment="machine", mechanics="isolation", joint_stress=["shoulder"], cns_load=1),
]

PLAN_333 = "33333333-3333-3333-3333-333333333333"
PLAN_444 = "44444444-4444-4444-4444-444444444444"
PLAN_011 = "00000000-0000-0000-0000-000000000011"
PLAN_022 = "00000000-0000-0000-0000-000000000022"

WORKOUT_PLANS = [
    dict(id=PLAN_333, name="Full Body A/B — Reboot", target_user_id="11111111-1111-1111-1111-111111111111", split_type="full_body",
         description="3 раза в неделю, чередование Дня А и Дня Б: Неделя 1 — А-Б-А, Неделя 2 — Б-А-Б. День А: база (присед/жим/подтягивания), День Б: тяги и руки"),
    dict(id=PLAN_444, name="Низ/Верх/Низ — Shape", target_user_id="22222222-2222-2222-2222-222222222222", split_type="upper_lower",
         description="3 дня: Низ (ягодицы/ноги) — Верх (грудь/осанка) — Низ (бёдра/пресс)"),
    dict(id=PLAN_011, name="Full Body A/B — Reboot", target_user_id="00000000-0000-0000-0000-000000000001", split_type="full_body",
         description="Spec alias для 000...001"),
    dict(id=PLAN_022, name="Низ/Верх/Низ — Shape", target_user_id="00000000-0000-0000-0000-000000000002", split_type="upper_lower",
         description="Spec alias для 000...002"),
]

# (day_number, exercise_name, order_index, target_sets, target_reps, suggested_method)
PLAN_333_EXERCISES = [
    (1, "Присед со штангой", 1, 4, "6-8", "pyramid"),
    (1, "Жим штанги лёжа", 2, 4, "6-8", "normal"),
    (1, "Подтягивания в гравитроне", 3, 3, "8-10", "rest_pause"),
    (1, "Жим сидя в тренажёре", 4, 3, "10-12", "normal"),
    (1, "Подъём штанги на бицепс", 5, 3, "10-12", "drop_set"),
    (1, "Жим гантели из-за головы", 6, 3, "10-12", "drop_set"),
    (1, "Гиперэкстензия", 7, 3, "15-20", "normal"),
    (2, "Румынская тяга с гантелями", 1, 4, "10-12", "pyramid"),
    (2, "Жим от груди в хаммере", 2, 3, "8-10", "normal"),
    (2, "Тяга Т-грифа с упором в грудь", 3, 3, "10-12", "normal"),
    (2, "Тяга каната к лицу (Face Pull)", 4, 3, "12-15", "drop_set"),
    (2, "Подъём гантелей на бицепс на наклонной", 5, 3, "10-12", "drop_set"),
    (2, "Разгибание на трицепс", 6, 3, "12-15", "drop_set"),
    (2, "Молотковые сгибания стоя", 7, 3, "12-15", "drop_set"),
]

PLAN_444_EXERCISES = [
    (1, "Ягодичный мостик", 1, 4, "10-12", "normal"),
    (1, "Болгарские сплит-приседы", 2, 3, "10-12 (на ногу)", "normal"),
    (1, "Жим ногами", 3, 3, "12-15", "normal"),
    (1, "Разведение ног сидя", 4, 3, "15-20", "drop_set"),
    (1, "Гиперэкстензия", 5, 3, "15", "normal"),
    (1, "Жим от груди в хаммере", 6, 2, "15-20", "drop_set"),
    (2, "Жим штанги лёжа", 1, 4, "8-10", "normal"),
    (2, "Жим гантелей на наклонной", 2, 3, "10-12", "normal"),
    (2, "Сведения в тренажёре «Бабочка»", 3, 3, "12-15", "drop_set"),
    (2, "Подтягивания в гравитроне", 4, 3, "10-12", "rest_pause"),
    (2, "Жим сидя в тренажёре", 5, 3, "12-15", "normal"),
    (2, "Тяга каната к лицу (Face Pull)", 6, 3, "15", "drop_set"),
    (3, "Румынская тяга", 1, 4, "10-12", "pyramid"),
    (3, "Сгибание ног лёжа", 2, 3, "12-15", "drop_set"),
    (3, "Выпады со штангой в Смите", 3, 3, "12 (на ногу)", "pyramid"),
    (3, "Отведение ноги с манжетой на нижнем блоке", 4, 3, "12-15 (на ногу)", "drop_set"),
    (3, "Разгибания ног сидя", 5, 3, "15", "drop_set"),
    (3, "Скручивания на пресс", 6, 3, "15-20", "amrap"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: SUPABASE_URL / SUPABASE_KEY not found in .env", file=sys.stderr)
        sys.exit(1)

    total_new_plan_ex = len(PLAN_333_EXERCISES) * 2 + len(PLAN_444_EXERCISES) * 2
    print(f"Target: {SUPABASE_URL}")
    print(f"Exercises to upsert: {len(EXERCISES)}")
    print(f"Workout plans to update: {len(WORKOUT_PLANS)}")
    print(f"Plan_exercises rows to insert (incl. aliases 011/022): {total_new_plan_ex}")

    if args.dry_run:
        print("\n--dry-run: no changes applied. Remove the flag to execute.")
        return

    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    print("\n1) Upserting exercises...")
    sb.table("exercises").upsert(EXERCISES, on_conflict="name").execute()

    print("2) Fetching exercise name -> id map...")
    names = [e["name"] for e in EXERCISES]
    rows = sb.table("exercises").select("id,name").in_("name", names).execute().data
    name_to_id = {r["name"]: r["id"] for r in rows}
    missing = [n for n in names if n not in name_to_id]
    if missing:
        print(f"ERROR: missing exercise ids for: {missing}", file=sys.stderr)
        sys.exit(1)

    print("3) Upserting workout_plans...")
    sb.table("workout_plans").upsert(WORKOUT_PLANS, on_conflict="id").execute()

    print("4) Deleting old plan_exercises for target plans...")
    sb.table("plan_exercises").delete().in_("plan_id", [PLAN_333, PLAN_444, PLAN_011, PLAN_022]).execute()

    def build_rows(plan_id, spec):
        out = []
        for day, ex_name, order_index, sets, reps, method in spec:
            out.append(dict(
                plan_id=plan_id, day_number=day, exercise_id=name_to_id[ex_name],
                order_index=order_index, target_sets=sets, target_reps=reps, suggested_method=method,
            ))
        return out

    print("5) Inserting new plan_exercises (333, 444, alias 011, alias 022)...")
    rows_to_insert = (
        build_rows(PLAN_333, PLAN_333_EXERCISES)
        + build_rows(PLAN_444, PLAN_444_EXERCISES)
        + build_rows(PLAN_011, PLAN_333_EXERCISES)
        + build_rows(PLAN_022, PLAN_444_EXERCISES)
    )
    sb.table("plan_exercises").insert(rows_to_insert).execute()

    print(f"\nDone. Inserted {len(rows_to_insert)} plan_exercises rows.")


if __name__ == "__main__":
    main()
