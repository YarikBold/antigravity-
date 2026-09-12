-- Antigravity Seed [4] — Full Body 🔥 (4-дневный цикл А-Б-В-Г)
-- Ярослав: Full Body 🔥 с акцентом на жим 85–90 кг + подтягивания + гибридное кардио
-- Олеся: Низ/Верх/Низ — Shape (без изменений)

INSERT INTO users (id, name, gender, goal, current_weight, target_weight, current_plan_id, schedule) VALUES
  ('11111111-1111-1111-1111-111111111111', 'Ярик',  'male',   'Сушка/сброс веса 78→72кг, жим 85-90кг, подтягивания с нуля', 78.0, 72.0, '33333333-3333-3333-3333-333333333333', '{1,3,5,6}'),
  ('22222222-2222-2222-2222-222222222222', 'Олеся', 'female', 'Качественный набор 46кг, акцент ягодицы/ноги/верх груди/осанка',              46.0, 49.0, '44444444-4444-4444-4444-444444444444', '{1,3,5}'),
  ('00000000-0000-0000-0000-000000000001', 'Ярик',  'male',   'Сушка/сброс веса 78→72кг', 78.0, 72.0, '33333333-3333-3333-3333-333333333333', '{1,3,5,6}'),
  ('00000000-0000-0000-0000-000000000002', 'Олеся', 'female', 'Набор 46кг ягодицы/ноги', 46.0, 49.0, '44444444-4444-4444-4444-444444444444', '{1,3,5}')
ON CONFLICT (id) DO UPDATE SET
  goal = EXCLUDED.goal,
  schedule = EXCLUDED.schedule,
  current_plan_id = EXCLUDED.current_plan_id,
  current_weight = EXCLUDED.current_weight,
  target_weight = EXCLUDED.target_weight;

-- ============================================================
-- УПРАЖНЕНИЯ (полный каталог)
-- ============================================================
INSERT INTO exercises (name, target_muscle, synergists, movement_pattern, equipment, mechanics, joint_stress, cns_load, media_url) VALUES
  ('Присед со штангой',            'quads',      ARRAY['glutes','hamstrings'], 'squat',           'barbell',   'compound',  ARRAY['knee','lumbar'],        5, NULL),
  ('Жим штанги лёжа',              'chest',      ARRAY['triceps','shoulders'], 'horizontal_push', 'barbell',   'compound',  ARRAY['shoulder','elbow'],    4, NULL),
  ('Тяга штанги в наклоне',        'back',       ARRAY['biceps','rear_delts'], 'horizontal_pull', 'barbell',   'compound',  ARRAY['lumbar','elbow'],      4, NULL),
  ('Румынская тяга',               'hamstrings', ARRAY['glutes','erector'],    'hinge',           'barbell',   'compound',  ARRAY['lumbar','hamstring'],  4, NULL),
  ('Жим гантелей на наклонной',    'chest',      ARRAY['triceps','shoulders'], 'horizontal_push', 'dumbbell',  'compound',  ARRAY['shoulder'],            3, NULL),
  ('Тяга верхнего блока',          'back',       ARRAY['biceps'],              'vertical_pull',   'cable',     'compound',  ARRAY['elbow','shoulder'],    3, NULL),
  ('Жим штанги стоя',              'shoulders',  ARRAY['triceps','core'],      'vertical_push',   'barbell',   'compound',  ARRAY['shoulder','lumbar'],   4, NULL),
  ('Ягодичный мостик',             'glutes',     ARRAY['hamstrings'],          'hinge',           'barbell',   'compound',  ARRAY[]::TEXT[],             2, NULL),
  ('Болгарские сплит-приседы',      'glutes',     ARRAY['quads','hamstrings'],  'lunge',           'dumbbell',  'compound',  ARRAY['knee'],                3, NULL),
  ('Жим ногами',                   'quads',      ARRAY['glutes'],              'squat',           'machine',   'compound',  ARRAY['knee'],                3, NULL),
  ('Сведение рук в кроссовере',    'chest',      ARRAY[]::TEXT[],              'isolation',       'cable',     'isolation', ARRAY['shoulder'],            1, NULL),
  ('Махи гантелей в стороны',      'shoulders',  ARRAY[]::TEXT[],              'isolation',       'dumbbell',  'isolation', ARRAY['shoulder'],            1, NULL),
  ('Сгибание рук с гантелями',     'biceps',     ARRAY[]::TEXT[],              'isolation',       'dumbbell',  'isolation', ARRAY['elbow'],               1, NULL),
  ('Разгибание на трицепс',        'triceps',    ARRAY[]::TEXT[],              'isolation',       'cable',     'isolation', ARRAY['elbow'],               1, NULL),
  ('Сгибание ног лёжа',            'hamstrings', ARRAY[]::TEXT[],              'isolation',       'machine',   'isolation', ARRAY['knee'],                1, NULL),
  ('Негативные подтягивания',       'back',       ARRAY['biceps'],              'vertical_pull',   'bodyweight','compound',  ARRAY['elbow','shoulder'],    3, NULL),
  ('Австралийские подтягивания',    'back',       ARRAY['biceps'],              'horizontal_pull', 'bodyweight','compound',  ARRAY['shoulder'],            2, NULL),
  ('Подтягивания с эспандером',     'back',       ARRAY['biceps'],              'vertical_pull',   'band',      'compound',  ARRAY['shoulder'],            2, NULL),
  ('Планка',                       'core',       ARRAY[]::TEXT[],              'core',            'bodyweight','isolation', ARRAY[]::TEXT[],             1, NULL),
  ('Скручивания на пресс',         'core',       ARRAY['hip_flexors'],         'core',            'bodyweight','isolation', ARRAY['lumbar'],             1, NULL),
  ('Отжимания',                    'chest',      ARRAY['triceps','shoulders'], 'horizontal_push', 'bodyweight','compound',  ARRAY['shoulder','elbow'],    2, NULL),
  ('Гиперэкстензия',               'hamstrings', ARRAY['glutes','erector'],    'hinge',           'bodyweight','isolation', ARRAY['lumbar'],             2, NULL),
  ('Подтягивания в гравитроне',                'back',       ARRAY['biceps'],              'vertical_pull',   'machine',   'compound',  ARRAY['elbow','shoulder'],    3, NULL),
  ('Жим сидя в тренажёре',                     'shoulders',  ARRAY['triceps'],             'vertical_push',   'machine',   'compound',  ARRAY['shoulder','elbow'],    3, NULL),
  ('Жим от груди в хаммере',                   'chest',      ARRAY['triceps','shoulders'], 'horizontal_push', 'machine',   'compound',  ARRAY['shoulder','elbow'],    3, NULL),
  ('Тяга Т-грифа с упором в грудь',            'back',       ARRAY['biceps','rear_delts'], 'horizontal_pull', 'machine',   'compound',  ARRAY['elbow'],               3, NULL),
  ('Румынская тяга с гантелями',               'hamstrings', ARRAY['glutes','erector'],    'hinge',           'dumbbell',  'compound',  ARRAY['lumbar','hamstring'],  4, NULL),
  ('Выпады со штангой в Смите',                'glutes',     ARRAY['quads','hamstrings'],  'lunge',           'barbell',   'compound',  ARRAY['knee'],                3, NULL),
  ('Тяга каната к лицу (Face Pull)',           'shoulders',  ARRAY['rear_delts'],          'isolation',       'cable',     'isolation', ARRAY['shoulder'],            1, NULL),
  ('Подъём штанги на бицепс',                  'biceps',     ARRAY[]::TEXT[],              'isolation',       'barbell',   'isolation', ARRAY['elbow'],               1, NULL),
  ('Подъём гантелей на бицепс на наклонной',   'biceps',     ARRAY[]::TEXT[],              'isolation',       'dumbbell',  'isolation', ARRAY['elbow'],               1, NULL),
  ('Молотковые сгибания стоя',                 'biceps',     ARRAY['forearms'],            'isolation',       'dumbbell',  'isolation', ARRAY['elbow'],               1, NULL),
  ('Жим гантели из-за головы',                 'triceps',    ARRAY[]::TEXT[],              'isolation',       'dumbbell',  'isolation', ARRAY['elbow','shoulder'],    1, NULL),
  ('Разведение ног сидя',                      'glutes',     ARRAY[]::TEXT[],              'isolation',       'machine',   'isolation', ARRAY[]::TEXT[],             1, NULL),
  ('Отведение ноги с манжетой на нижнем блоке','glutes',     ARRAY[]::TEXT[],              'isolation',       'cable',     'isolation', ARRAY[]::TEXT[],             1, NULL),
  ('Разгибания ног сидя',                      'quads',      ARRAY[]::TEXT[],              'isolation',       'machine',   'isolation', ARRAY['knee'],                1, NULL),
  ('Сведения в тренажёре «Бабочка»',           'chest',      ARRAY[]::TEXT[],              'isolation',       'machine',   'isolation', ARRAY['shoulder'],            1, NULL),
  -- Новые упражнения для плана Full Body 🔥
  ('Тяга гантели в наклоне с упором',          'back',       ARRAY['biceps','rear_delts'], 'horizontal_pull', 'dumbbell',  'compound',  ARRAY['lumbar','elbow'],      3, NULL),
  ('Махи с гантелями стоя',                    'shoulders',  ARRAY[]::TEXT[],              'isolation',       'dumbbell',  'isolation', ARRAY['shoulder'],            1, NULL),
  ('Кубковый присед',                          'quads',      ARRAY['glutes','core'],       'squat',           'dumbbell',  'compound',  ARRAY['knee'],                3, NULL),
  ('Подтягивания с резиной',                   'back',       ARRAY['biceps'],              'vertical_pull',   'band',      'compound',  ARRAY['elbow','shoulder'],    3, NULL),
  ('Ходьба в гору (LISS)',                     'cardio',     ARRAY['glutes','hamstrings'], 'cardio',          'machine',    'isolation', ARRAY[]::TEXT[],             1, NULL),
  ('Махи гирей',                               'hamstrings', ARRAY['glutes','core','shoulders'], 'conditioning', 'kettlebell', 'compound', ARRAY['lumbar','shoulder'],  3, NULL),
  ('Отжимания от пола (MetCon)',               'chest',      ARRAY['triceps','shoulders','core'], 'conditioning', 'bodyweight', 'compound', ARRAY['shoulder','elbow'],  2, NULL),
  ('Кубковые приседания (MetCon)',             'quads',      ARRAY['glutes','core'],       'conditioning',    'kettlebell', 'compound',  ARRAY['knee','lumbar'],      3, NULL),
  ('Скалолаз (Mountain Climbers)',             'core',       ARRAY['hip_flexors','shoulders'], 'conditioning', 'bodyweight', 'compound', ARRAY[]::TEXT[],             2, NULL),
  ('Велотренажер / Заминка (LISS)',            'cardio',     ARRAY['quads','hamstrings'],  'cardio',          'machine',    'isolation', ARRAY[]::TEXT[],             1, NULL)
ON CONFLICT (name) DO NOTHING;

-- Гравитрон + подтягивания с резиной: инвертированная физика противовеса
UPDATE exercises SET is_assisted = true WHERE name IN ('Подтягивания в гравитроне', 'Подтягивания с резиной');

-- ============================================================
-- ПЛАНЫ ТРЕНИРОВОК
-- ============================================================
INSERT INTO workout_plans (id, name, target_user_id, split_type, description) VALUES
  ('33333333-3333-3333-3333-333333333333', 'Full Body 🔥', '11111111-1111-1111-1111-111111111111', 'full_body',   '4-дневный цикл А-Б-В-Г: тяжёлый жим + спина → ноги + вертикаль → скоростной жим + руки → гибридное кардио. Цель: жим 85–90 кг, подтягивания с нуля.'),
  ('44444444-4444-4444-4444-444444444444', 'Низ/Верх/Низ — Shape',   '22222222-2222-2222-2222-222222222222', 'upper_lower', '3 дня: Низ (ягодицы/ноги) — Верх (грудь/осанка) — Низ (бёдра/пресс)'),
  ('00000000-0000-0000-0000-000000000011', 'Full Body 🔥', '00000000-0000-0000-0000-000000000001', 'full_body',   'Alias для 000...001'),
  ('00000000-0000-0000-0000-000000000022', 'Низ/Верх/Низ — Shape',   '00000000-0000-0000-0000-000000000002', 'upper_lower', 'Alias для 000...002')
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name,
  target_user_id = EXCLUDED.target_user_id,
  split_type = EXCLUDED.split_type,
  description = EXCLUDED.description;

-- ============================================================
-- FULL BODY 🔥 — 4-дневный цикл Ярика (план 333)
-- ============================================================
DELETE FROM plan_exercises WHERE plan_id IN (
  '33333333-3333-3333-3333-333333333333',
  '00000000-0000-0000-0000-000000000011'
);

-- День 1 (А) — Тяжёлый Жим + Сила Спины
INSERT INTO plan_exercises (plan_id, day_number, exercise_id, order_index, target_sets, target_reps, suggested_method) VALUES
  ('33333333-3333-3333-3333-333333333333', 1, (SELECT id FROM exercises WHERE name='Жим штанги лёжа'),                      1, 4, '4-5',   'normal'),
  ('33333333-3333-3333-3333-333333333333', 1, (SELECT id FROM exercises WHERE name='Подтягивания в гравитроне'),             2, 4, '4-5',   'normal'),
  ('33333333-3333-3333-3333-333333333333', 1, (SELECT id FROM exercises WHERE name='Жим ногами'),                            3, 3, '8-10',  'normal'),
  ('33333333-3333-3333-3333-333333333333', 1, (SELECT id FROM exercises WHERE name='Тяга гантели в наклоне с упором'),       4, 3, '8-10',  'normal'),
  ('33333333-3333-3333-3333-333333333333', 1, (SELECT id FROM exercises WHERE name='Махи с гантелями стоя'),                 5, 3, '12-15', 'normal');

-- День 2 (Б) — Ноги + Вертикальная тяга + Жим стоя
INSERT INTO plan_exercises (plan_id, day_number, exercise_id, order_index, target_sets, target_reps, suggested_method) VALUES
  ('33333333-3333-3333-3333-333333333333', 2, (SELECT id FROM exercises WHERE name='Кубковый присед'),                      1, 3, '6-8',   'normal'),
  ('33333333-3333-3333-3333-333333333333', 2, (SELECT id FROM exercises WHERE name='Сгибание ног лёжа'),                    2, 3, '10-12', 'normal'),
  ('33333333-3333-3333-3333-333333333333', 2, (SELECT id FROM exercises WHERE name='Австралийские подтягивания'),             3, 3, '10-12', 'normal'),
  ('33333333-3333-3333-3333-333333333333', 2, (SELECT id FROM exercises WHERE name='Жим штанги стоя'),                       4, 3, '5-8',   'pyramid'),
  ('33333333-3333-3333-3333-333333333333', 2, (SELECT id FROM exercises WHERE name='Скручивания на пресс'),                  5, 3, '15-20', 'normal');

-- День 3 (В) — Скоростной Жим + Объём Турника + Руки
INSERT INTO plan_exercises (plan_id, day_number, exercise_id, order_index, target_sets, target_reps, suggested_method) VALUES
  ('33333333-3333-3333-3333-333333333333', 3, (SELECT id FROM exercises WHERE name='Жим штанги лёжа'),                      1, 4, '6-8',   'normal'),
  ('33333333-3333-3333-3333-333333333333', 3, (SELECT id FROM exercises WHERE name='Подтягивания с резиной'),                2, 4, '6-8',   'normal'),
  ('33333333-3333-3333-3333-333333333333', 3, (SELECT id FROM exercises WHERE name='Тяга верхнего блока'),                   3, 3, '8-10',  'normal'),
  ('33333333-3333-3333-3333-333333333333', 3, (SELECT id FROM exercises WHERE name='Подъём штанги на бицепс'),               4, 3, '10-12', 'normal'),
  ('33333333-3333-3333-3333-333333333333', 3, (SELECT id FROM exercises WHERE name='Разгибание на трицепс'),                 5, 3, '10-12', 'normal');

-- День 4 (Г) — Гибридное кардио (45–50 минут)
INSERT INTO plan_exercises (plan_id, day_number, exercise_id, order_index, target_sets, target_reps, suggested_method) VALUES
  ('33333333-3333-3333-3333-333333333333', 4, (SELECT id FROM exercises WHERE name='Ходьба в гору (LISS)'),                 1, 1, '15 мин',    'normal'),
  ('33333333-3333-3333-3333-333333333333', 4, (SELECT id FROM exercises WHERE name='Махи гирей'),                           2, 3, '18',        'emom'),
  ('33333333-3333-3333-3333-333333333333', 4, (SELECT id FROM exercises WHERE name='Отжимания от пола (MetCon)'),            3, 3, '15',        'emom'),
  ('33333333-3333-3333-3333-333333333333', 4, (SELECT id FROM exercises WHERE name='Кубковые приседания (MetCon)'),          4, 3, '14',        'emom'),
  ('33333333-3333-3333-3333-333333333333', 4, (SELECT id FROM exercises WHERE name='Скалолаз (Mountain Climbers)'),          5, 3, '35 сек',    'emom'),
  ('33333333-3333-3333-3333-333333333333', 4, (SELECT id FROM exercises WHERE name='Велотренажер / Заминка (LISS)'),         6, 1, '15-20 мин', 'normal');

-- Alias план для 000...001
INSERT INTO plan_exercises (plan_id, day_number, exercise_id, order_index, target_sets, target_reps, suggested_method)
SELECT '00000000-0000-0000-0000-000000000011', day_number, exercise_id, order_index, target_sets, target_reps, suggested_method
FROM plan_exercises WHERE plan_id='33333333-3333-3333-3333-333333333333' ON CONFLICT DO NOTHING;

-- ============================================================
-- ОЛЕСЯ: Низ/Верх/Низ — Shape (план 444, без изменений)
-- ============================================================
DELETE FROM plan_exercises WHERE plan_id IN (
  '44444444-4444-4444-4444-444444444444',
  '00000000-0000-0000-0000-000000000022'
);

-- День 1 = Низ
INSERT INTO plan_exercises (plan_id, day_number, exercise_id, order_index, target_sets, target_reps, suggested_method) VALUES
  ('44444444-4444-4444-4444-444444444444', 1, (SELECT id FROM exercises WHERE name='Ягодичный мостик'),                    1, 4, '10-12', 'normal'),
  ('44444444-4444-4444-4444-444444444444', 1, (SELECT id FROM exercises WHERE name='Болгарские сплит-приседы'),            2, 3, '10-12 (на ногу)', 'normal'),
  ('44444444-4444-4444-4444-444444444444', 1, (SELECT id FROM exercises WHERE name='Жим ногами'),                          3, 3, '12-15', 'normal'),
  ('44444444-4444-4444-4444-444444444444', 1, (SELECT id FROM exercises WHERE name='Разведение ног сидя'),                 4, 3, '15-20', 'drop_set'),
  ('44444444-4444-4444-4444-444444444444', 1, (SELECT id FROM exercises WHERE name='Гиперэкстензия'),                      5, 3, '15',    'normal'),
  ('44444444-4444-4444-4444-444444444444', 1, (SELECT id FROM exercises WHERE name='Жим от груди в хаммере'),              6, 2, '15-20', 'drop_set'),
  -- День 2 = Верх
  ('44444444-4444-4444-4444-444444444444', 2, (SELECT id FROM exercises WHERE name='Жим штанги лёжа'),                     1, 4, '8-10',  'normal'),
  ('44444444-4444-4444-4444-444444444444', 2, (SELECT id FROM exercises WHERE name='Жим гантелей на наклонной'),           2, 3, '10-12', 'normal'),
  ('44444444-4444-4444-4444-444444444444', 2, (SELECT id FROM exercises WHERE name='Сведения в тренажёре «Бабочка»'),      3, 3, '12-15', 'drop_set'),
  ('44444444-4444-4444-4444-444444444444', 2, (SELECT id FROM exercises WHERE name='Подтягивания в гравитроне'),           4, 3, '10-12', 'rest_pause'),
  ('44444444-4444-4444-4444-444444444444', 2, (SELECT id FROM exercises WHERE name='Жим сидя в тренажёре'),                5, 3, '12-15', 'normal'),
  ('44444444-4444-4444-4444-444444444444', 2, (SELECT id FROM exercises WHERE name='Тяга каната к лицу (Face Pull)'),      6, 3, '15',    'drop_set'),
  -- День 3 = Низ (бёдра/пресс)
  ('44444444-4444-4444-4444-444444444444', 3, (SELECT id FROM exercises WHERE name='Румынская тяга'),                      1, 4, '10-12', 'pyramid'),
  ('44444444-4444-4444-4444-444444444444', 3, (SELECT id FROM exercises WHERE name='Сгибание ног лёжа'),                   2, 3, '12-15', 'drop_set'),
  ('44444444-4444-4444-4444-444444444444', 3, (SELECT id FROM exercises WHERE name='Выпады со штангой в Смите'),           3, 3, '12 (на ногу)', 'pyramid'),
  ('44444444-4444-4444-4444-444444444444', 3, (SELECT id FROM exercises WHERE name='Отведение ноги с манжетой на нижнем блоке'), 4, 3, '12-15 (на ногу)', 'drop_set'),
  ('44444444-4444-4444-4444-444444444444', 3, (SELECT id FROM exercises WHERE name='Разгибания ног сидя'),                 5, 3, '15',    'drop_set'),
  ('44444444-4444-4444-4444-444444444444', 3, (SELECT id FROM exercises WHERE name='Скручивания на пресс'),                6, 3, '15-20', 'amrap')
ON CONFLICT DO NOTHING;

INSERT INTO plan_exercises (plan_id, day_number, exercise_id, order_index, target_sets, target_reps, suggested_method)
SELECT '00000000-0000-0000-0000-000000000022', day_number, exercise_id, order_index, target_sets, target_reps, suggested_method FROM plan_exercises WHERE plan_id='44444444-4444-4444-4444-444444444444' ON CONFLICT DO NOTHING;

-- Кардио-день 4 для Олеси (план 444) — такой же набор
INSERT INTO plan_exercises (plan_id, day_number, exercise_id, order_index, target_sets, target_reps, suggested_method) VALUES
  ('44444444-4444-4444-4444-444444444444', 4, (SELECT id FROM exercises WHERE name='Ходьба в гору (LISS)'),          1, 1, '15 мин',    'normal'),
  ('44444444-4444-4444-4444-444444444444', 4, (SELECT id FROM exercises WHERE name='Махи гирей'),                    2, 3, '18',        'emom'),
  ('44444444-4444-4444-4444-444444444444', 4, (SELECT id FROM exercises WHERE name='Отжимания от пола (MetCon)'),    3, 3, '15',        'emom'),
  ('44444444-4444-4444-4444-444444444444', 4, (SELECT id FROM exercises WHERE name='Кубковые приседания (MetCon)'),  4, 3, '14',        'emom'),
  ('44444444-4444-4444-4444-444444444444', 4, (SELECT id FROM exercises WHERE name='Скалолаз (Mountain Climbers)'),  5, 3, '35 сек',    'emom'),
  ('44444444-4444-4444-4444-444444444444', 4, (SELECT id FROM exercises WHERE name='Велотренажер / Заминка (LISS)'), 6, 1, '15-20 мин', 'normal')
ON CONFLICT DO NOTHING;

INSERT INTO plan_exercises (plan_id, day_number, exercise_id, order_index, target_sets, target_reps, suggested_method)
SELECT '00000000-0000-0000-0000-000000000022', day_number, exercise_id, order_index, target_sets, target_reps, suggested_method
FROM plan_exercises WHERE plan_id='44444444-4444-4444-4444-444444444444' AND day_number=4 ON CONFLICT DO NOTHING;

-- ============================================================
-- Демо-история Ярика (календарь «История» сразу с зелёными днями)
-- ============================================================
DELETE FROM workout_sets WHERE log_id IN (
  'a1111111-1111-4111-8111-111111111001',
  'a1111111-1111-4111-8111-111111111002',
  'a1111111-1111-4111-8111-111111111003'
);
DELETE FROM workout_logs WHERE id IN (
  'a1111111-1111-4111-8111-111111111001',
  'a1111111-1111-4111-8111-111111111002',
  'a1111111-1111-4111-8111-111111111003'
);
INSERT INTO workout_logs (id, user_id, plan_id, date, day_number, completed, session_type, total_duration_minutes, notes) VALUES
  ('a1111111-1111-4111-8111-111111111001', '11111111-1111-1111-1111-111111111111', '33333333-3333-3333-3333-333333333333', '2026-09-08', 1, true, 'strength', 48, 'День А — тяжёлый жим'),
  ('a1111111-1111-4111-8111-111111111002', '11111111-1111-1111-1111-111111111111', '33333333-3333-3333-3333-333333333333', '2026-09-10', 2, true, 'strength', 52, 'День Б — ноги + вертикаль'),
  ('a1111111-1111-4111-8111-111111111003', '11111111-1111-1111-1111-111111111111', '33333333-3333-3333-3333-333333333333', '2026-09-12', 4, true, 'cardio',    47, 'День Г — гибридное кардио')
ON CONFLICT (id) DO NOTHING;

INSERT INTO workout_sets (log_id, exercise_id, set_number, set_type, weight, reps, rir) VALUES
  ('a1111111-1111-4111-8111-111111111001', (SELECT id FROM exercises WHERE name='Жим штанги лёжа'), 1, 'normal', 50, 8, 2),
  ('a1111111-1111-4111-8111-111111111001', (SELECT id FROM exercises WHERE name='Жим штанги лёжа'), 2, 'normal', 50, 8, 2),
  ('a1111111-1111-4111-8111-111111111001', (SELECT id FROM exercises WHERE name='Подтягивания в гравитроне'), 1, 'normal', 25, 6, 1),
  ('a1111111-1111-4111-8111-111111111001', (SELECT id FROM exercises WHERE name='Подтягивания в гравитроне'), 2, 'normal', 25, 6, 1),
  ('a1111111-1111-4111-8111-111111111001', (SELECT id FROM exercises WHERE name='Жим ногами'), 1, 'normal', 80, 10, 2),
  ('a1111111-1111-4111-8111-111111111002', (SELECT id FROM exercises WHERE name='Кубковый присед'), 1, 'normal', 20, 8, 2),
  ('a1111111-1111-4111-8111-111111111002', (SELECT id FROM exercises WHERE name='Сгибание ног лёжа'), 1, 'normal', 25, 12, 2),
  ('a1111111-1111-4111-8111-111111111002', (SELECT id FROM exercises WHERE name='Жим штанги стоя'), 1, 'pyramid', 30, 5, 1)
ON CONFLICT DO NOTHING;

INSERT INTO workout_sets (log_id, exercise_id, set_number, set_type, weight, reps, rir, duration_seconds, completed_rounds) VALUES
  ('a1111111-1111-4111-8111-111111111003', (SELECT id FROM exercises WHERE name='Ходьба в гору (LISS)'), 1, 'normal', 1.5, NULL, 2, 900, NULL),
  ('a1111111-1111-4111-8111-111111111003', (SELECT id FROM exercises WHERE name='Махи гирей'), 1, 'emom', 16, 18, 2, NULL, 3),
  ('a1111111-1111-4111-8111-111111111003', (SELECT id FROM exercises WHERE name='Велотренажер / Заминка (LISS)'), 1, 'normal', NULL, NULL, 2, 1080, NULL)
ON CONFLICT DO NOTHING;
