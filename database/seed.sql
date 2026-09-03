-- Antigravity Seed [3] — детерминированные UUID для 2 профилей
-- Обновление планов по документу «план тренировок»: Ярослав — Full Body A/B (чередование Дня А и Дня Б), Олеся — Низ/Верх/Низ
-- Spec example: 00000000-0000-0000-0000-000000000001/002 + legacy 111/222 для обратной совместимости

INSERT INTO users (id, name, gender, goal, current_weight, target_weight) VALUES
  ('11111111-1111-1111-1111-111111111111', 'Ярик',  'male',   'Сушка/сброс веса 78→72кг, убрать отечность ног, прогресс в подтягиваниях', 78.0, 72.0),
  ('22222222-2222-2222-2222-222222222222', 'Олеся', 'female', 'Качественный набор 46кг, акцент ягодицы/ноги/верх груди/осанка',              46.0, 49.0),
  ('00000000-0000-0000-0000-000000000001', 'Ярик',  'male',   'Сушка/сброс веса 78→72кг', 78.0, 72.0),
  ('00000000-0000-0000-0000-000000000002', 'Олеся', 'female', 'Набор 46кг ягодицы/ноги', 46.0, 49.0)
ON CONFLICT (id) DO NOTHING;

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
  -- Новые упражнения (план «план тренировок»)
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
  ('Сведения в тренажёре «Бабочка»',           'chest',      ARRAY[]::TEXT[],              'isolation',       'machine',   'isolation', ARRAY['shoulder'],            1, NULL)
ON CONFLICT (name) DO NOTHING;

INSERT INTO workout_plans (id, name, target_user_id, split_type, description) VALUES
  ('33333333-3333-3333-3333-333333333333', 'Full Body A/B — Reboot', '11111111-1111-1111-1111-111111111111', 'full_body',   '3 раза в неделю, чередование Дня А и Дня Б: Неделя 1 — А-Б-А, Неделя 2 — Б-А-Б. День А: база (присед/жим/подтягивания), День Б: тяги и руки'),
  ('44444444-4444-4444-4444-444444444444', 'Низ/Верх/Низ — Shape',   '22222222-2222-2222-2222-222222222222', 'upper_lower', '3 дня: Низ (ягодицы/ноги) — Верх (грудь/осанка) — Низ (бёдра/пресс)'),
  ('00000000-0000-0000-0000-000000000011', 'Full Body A/B — Reboot', '00000000-0000-0000-0000-000000000001', 'full_body',   'Spec alias для 000...001'),
  ('00000000-0000-0000-0000-000000000022', 'Низ/Верх/Низ — Shape',   '00000000-0000-0000-0000-000000000002', 'upper_lower', 'Spec alias для 000...002')
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name,
  target_user_id = EXCLUDED.target_user_id,
  split_type = EXCLUDED.split_type,
  description = EXCLUDED.description;

-- Полная перезапись составов планов (idempotent re-seed)
DELETE FROM plan_exercises WHERE plan_id IN (
  '33333333-3333-3333-3333-333333333333',
  '44444444-4444-4444-4444-444444444444',
  '00000000-0000-0000-0000-000000000011',
  '00000000-0000-0000-0000-000000000022'
);

-- Plan 333 (Full Body A/B) — День 1 = День А
INSERT INTO plan_exercises (plan_id, day_number, exercise_id, order_index, target_sets, target_reps, suggested_method) VALUES
  ('33333333-3333-3333-3333-333333333333', 1, (SELECT id FROM exercises WHERE name='Присед со штангой'),                    1, 4, '6-8',   'pyramid'),
  ('33333333-3333-3333-3333-333333333333', 1, (SELECT id FROM exercises WHERE name='Жим штанги лёжа'),                     2, 4, '6-8',   'normal'),
  ('33333333-3333-3333-3333-333333333333', 1, (SELECT id FROM exercises WHERE name='Подтягивания в гравитроне'),           3, 3, '8-10',  'rest_pause'),
  ('33333333-3333-3333-3333-333333333333', 1, (SELECT id FROM exercises WHERE name='Жим сидя в тренажёре'),                4, 3, '10-12', 'normal'),
  ('33333333-3333-3333-3333-333333333333', 1, (SELECT id FROM exercises WHERE name='Подъём штанги на бицепс'),             5, 3, '10-12', 'drop_set'),
  ('33333333-3333-3333-3333-333333333333', 1, (SELECT id FROM exercises WHERE name='Жим гантели из-за головы'),            6, 3, '10-12', 'drop_set'),
  ('33333333-3333-3333-3333-333333333333', 1, (SELECT id FROM exercises WHERE name='Гиперэкстензия'),                      7, 3, '15-20', 'normal'),
  -- День 2 = День Б
  ('33333333-3333-3333-3333-333333333333', 2, (SELECT id FROM exercises WHERE name='Румынская тяга с гантелями'),          1, 4, '10-12', 'pyramid'),
  ('33333333-3333-3333-3333-333333333333', 2, (SELECT id FROM exercises WHERE name='Жим от груди в хаммере'),              2, 3, '8-10',  'normal'),
  ('33333333-3333-3333-3333-333333333333', 2, (SELECT id FROM exercises WHERE name='Тяга Т-грифа с упором в грудь'),       3, 3, '10-12', 'normal'),
  ('33333333-3333-3333-3333-333333333333', 2, (SELECT id FROM exercises WHERE name='Тяга каната к лицу (Face Pull)'),      4, 3, '12-15', 'drop_set'),
  ('33333333-3333-3333-3333-333333333333', 2, (SELECT id FROM exercises WHERE name='Подъём гантелей на бицепс на наклонной'), 5, 3, '10-12', 'drop_set'),
  ('33333333-3333-3333-3333-333333333333', 2, (SELECT id FROM exercises WHERE name='Разгибание на трицепс'),               6, 3, '12-15', 'drop_set'),
  ('33333333-3333-3333-3333-333333333333', 2, (SELECT id FROM exercises WHERE name='Молотковые сгибания стоя'),            7, 3, '12-15', 'drop_set')
ON CONFLICT DO NOTHING;

INSERT INTO plan_exercises (plan_id, day_number, exercise_id, order_index, target_sets, target_reps, suggested_method)
SELECT '00000000-0000-0000-0000-000000000011', day_number, exercise_id, order_index, target_sets, target_reps, suggested_method FROM plan_exercises WHERE plan_id='33333333-3333-3333-3333-333333333333' ON CONFLICT DO NOTHING;

-- Plan 444 (Низ/Верх/Низ) — День 1 = Низ
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
