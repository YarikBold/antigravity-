-- Antigravity — Hybrid Cardio Module Migration
-- seed_cardio.sql: Schema changes + cardio exercises + cardio day for all plans

-- ============================================================
-- 1. SCHEMA CHANGES
-- ============================================================

-- 1a. Extend movement_pattern CHECK to include 'cardio' and 'conditioning'
ALTER TABLE exercises DROP CONSTRAINT IF EXISTS exercises_movement_pattern_check;
ALTER TABLE exercises ADD CONSTRAINT exercises_movement_pattern_check
  CHECK (movement_pattern IN (
    'horizontal_push','vertical_push','horizontal_pull','vertical_pull',
    'squat','hinge','lunge','isolation','core',
    'cardio','conditioning'
  ));

-- 1b. Make workout_sets.weight and reps nullable for cardio logs
ALTER TABLE workout_sets ALTER COLUMN weight DROP NOT NULL;
ALTER TABLE workout_sets ALTER COLUMN weight SET DEFAULT NULL;
ALTER TABLE workout_sets ALTER COLUMN reps DROP NOT NULL;
ALTER TABLE workout_sets ALTER COLUMN reps SET DEFAULT NULL;

-- 1c. Add duration/rounds columns to workout_sets
ALTER TABLE workout_sets ADD COLUMN IF NOT EXISTS duration_seconds INT;
ALTER TABLE workout_sets ADD COLUMN IF NOT EXISTS completed_rounds INT;

-- 1d. Extend workout_sets.set_type to include 'emom'
ALTER TABLE workout_sets DROP CONSTRAINT IF EXISTS workout_sets_set_type_check;
ALTER TABLE workout_sets ADD CONSTRAINT workout_sets_set_type_check
  CHECK (set_type IN ('normal','drop_set','rest_pause','pyramid','emom'));

-- 1e. Add session metadata to workout_logs
ALTER TABLE workout_logs ADD COLUMN IF NOT EXISTS session_type TEXT NOT NULL DEFAULT 'strength';
ALTER TABLE workout_logs ADD COLUMN IF NOT EXISTS total_duration_minutes INT;
ALTER TABLE workout_logs ADD COLUMN IF NOT EXISTS perceived_effort_rpe INT;
ALTER TABLE workout_logs ADD COLUMN IF NOT EXISTS notes TEXT;

-- ============================================================
-- 2. CARDIO & CONDITIONING EXERCISES
-- ============================================================

INSERT INTO exercises (name, target_muscle, synergists, movement_pattern, equipment, mechanics, joint_stress, cns_load, media_url) VALUES
  ('Ходьба в гору (LISS)',              'cardio',       ARRAY['glutes','hamstrings'],     'cardio',        'machine',    'isolation', ARRAY[]::TEXT[], 1, NULL),
  ('Махи гирей',                        'hamstrings',   ARRAY['glutes','core','shoulders'],'conditioning', 'kettlebell', 'compound',  ARRAY['lumbar','shoulder'], 3, NULL),
  ('Отжимания от пола (MetCon)',         'chest',        ARRAY['triceps','shoulders','core'],'conditioning','bodyweight', 'compound',  ARRAY['shoulder','elbow'],  2, NULL),
  ('Кубковые приседания (MetCon)',       'quads',        ARRAY['glutes','core'],            'conditioning', 'kettlebell', 'compound',  ARRAY['knee','lumbar'],     3, NULL),
  ('Скалолаз (Mountain Climbers)',       'core',         ARRAY['hip_flexors','shoulders'],  'conditioning', 'bodyweight', 'compound',  ARRAY[]::TEXT[],            2, NULL),
  ('Велотренажер / Заминка (LISS)',      'cardio',       ARRAY['quads','hamstrings'],       'cardio',       'machine',    'isolation', ARRAY[]::TEXT[],            1, NULL)
ON CONFLICT (name) DO NOTHING;

-- ============================================================
-- 3. ATTACH CARDIO DAY (day_number=4) TO ALL PLANS
-- ============================================================

-- Clean up existing cardio day entries (idempotent re-seed)
DELETE FROM plan_exercises WHERE day_number = 4 AND plan_id IN (
  '33333333-3333-3333-3333-333333333333',
  '44444444-4444-4444-4444-444444444444',
  '00000000-0000-0000-0000-000000000011',
  '00000000-0000-0000-0000-000000000022'
);

-- Plan 333 (Ярик Full Body A/B) — Day 4: Hybrid Cardio
INSERT INTO plan_exercises (plan_id, day_number, exercise_id, order_index, target_sets, target_reps, suggested_method) VALUES
  -- Phase 1: LISS Entry (15 min treadmill incline walk)
  ('33333333-3333-3333-3333-333333333333', 4, (SELECT id FROM exercises WHERE name='Ходьба в гору (LISS)'),              1, 1, '15 мин', 'normal'),
  -- Phase 2: EMOM MetCon (3 rounds x 5 stations = 15 min)
  ('33333333-3333-3333-3333-333333333333', 4, (SELECT id FROM exercises WHERE name='Махи гирей'),                        2, 3, '18',     'emom'),
  ('33333333-3333-3333-3333-333333333333', 4, (SELECT id FROM exercises WHERE name='Отжимания от пола (MetCon)'),         3, 3, '15',     'emom'),
  ('33333333-3333-3333-3333-333333333333', 4, (SELECT id FROM exercises WHERE name='Кубковые приседания (MetCon)'),       4, 3, '14',     'emom'),
  ('33333333-3333-3333-3333-333333333333', 4, (SELECT id FROM exercises WHERE name='Скалолаз (Mountain Climbers)'),       5, 3, '35 сек', 'emom'),
  -- Phase 3: LISS Flush (15-20 min bike/elliptical)
  ('33333333-3333-3333-3333-333333333333', 4, (SELECT id FROM exercises WHERE name='Велотренажер / Заминка (LISS)'),      6, 1, '15-20 мин', 'normal')
ON CONFLICT DO NOTHING;

-- Plan 444 (Олеся Низ/Верх/Низ) — Day 4: Hybrid Cardio (same structure)
INSERT INTO plan_exercises (plan_id, day_number, exercise_id, order_index, target_sets, target_reps, suggested_method) VALUES
  ('44444444-4444-4444-4444-444444444444', 4, (SELECT id FROM exercises WHERE name='Ходьба в гору (LISS)'),              1, 1, '15 мин', 'normal'),
  ('44444444-4444-4444-4444-444444444444', 4, (SELECT id FROM exercises WHERE name='Махи гирей'),                        2, 3, '18',     'emom'),
  ('44444444-4444-4444-4444-444444444444', 4, (SELECT id FROM exercises WHERE name='Отжимания от пола (MetCon)'),         3, 3, '15',     'emom'),
  ('44444444-4444-4444-4444-444444444444', 4, (SELECT id FROM exercises WHERE name='Кубковые приседания (MetCon)'),       4, 3, '14',     'emom'),
  ('44444444-4444-4444-4444-444444444444', 4, (SELECT id FROM exercises WHERE name='Скалолаз (Mountain Climbers)'),       5, 3, '35 сек', 'emom'),
  ('44444444-4444-4444-4444-444444444444', 4, (SELECT id FROM exercises WHERE name='Велотренажер / Заминка (LISS)'),      6, 1, '15-20 мин', 'normal')
ON CONFLICT DO NOTHING;

-- Alias plans: copy cardio day from primary plans
INSERT INTO plan_exercises (plan_id, day_number, exercise_id, order_index, target_sets, target_reps, suggested_method)
SELECT '00000000-0000-0000-0000-000000000011', day_number, exercise_id, order_index, target_sets, target_reps, suggested_method
FROM plan_exercises WHERE plan_id='33333333-3333-3333-3333-333333333333' AND day_number=4
ON CONFLICT DO NOTHING;

INSERT INTO plan_exercises (plan_id, day_number, exercise_id, order_index, target_sets, target_reps, suggested_method)
SELECT '00000000-0000-0000-0000-000000000022', day_number, exercise_id, order_index, target_sets, target_reps, suggested_method
FROM plan_exercises WHERE plan_id='44444444-4444-4444-4444-444444444444' AND day_number=4
ON CONFLICT DO NOTHING;
