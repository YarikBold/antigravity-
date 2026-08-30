-- Antigravity Seed — 2 профиля, 22 упражнения, 2 программы

-- Users
INSERT INTO users (id, name, gender, goal, current_weight, target_weight) VALUES
  ('11111111-1111-1111-1111-111111111111', 'Ярик',  'male',   'Сушка/сброс веса 78→72кг, убрать отечность ног, прогресс в подтягиваниях', 78.0, 72.0),
  ('22222222-2222-2222-2222-222222222222', 'Олеся', 'female', 'Качественный набор 46кг, акцент ягодицы/ноги/верх груди/осанка',              46.0, 49.0)
ON CONFLICT (id) DO NOTHING;

-- Exercises (22 с биомеханикой)
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
  ('Гиперэкстензия',               'hamstrings', ARRAY['glutes','erector'],    'hinge',           'bodyweight','isolation', ARRAY['lumbar'],             2, NULL)
ON CONFLICT (name) DO NOTHING;

-- Plans
INSERT INTO workout_plans (id, name, target_user_id, split_type, description) VALUES
  ('33333333-3333-3333-3333-333333333333', 'Full Body — Reboot', '11111111-1111-1111-1111-111111111111', 'full_body', '3 дня Full Body для Ярика: база + прогресс подтягиваний, жиросжигание'),
  ('44444444-4444-4444-4444-444444444444', 'Upper/Lower — Shape', '22222222-2222-2222-2222-222222222222', 'upper_lower', '3 дня Низ/Верх/Низ для Олеси: ягодицы, ноги, верх груди, осанка')
ON CONFLICT (id) DO NOTHING;

-- Plan exercises: Full Body (3 дня)
-- День 1
INSERT INTO plan_exercises (plan_id, day_number, exercise_id, order_index, target_sets, target_reps, suggested_method) VALUES
  ('33333333-3333-3333-3333-333333333333', 1, (SELECT id FROM exercises WHERE name='Присед со штангой'), 1, 3, '8-10', 'normal'),
  ('33333333-3333-3333-3333-333333333333', 1, (SELECT id FROM exercises WHERE name='Жим штанги лёжа'), 2, 3, '8-10', 'normal'),
  ('33333333-3333-3333-3333-333333333333', 1, (SELECT id FROM exercises WHERE name='Австралийские подтягивания'), 3, 3, '8-10', 'normal'),
  ('33333333-3333-3333-3333-333333333333', 1, (SELECT id FROM exercises WHERE name='Махи гантелей в стороны'), 4, 3, '12-15', 'normal'),
  ('33333333-3333-3333-3333-333333333333', 1, (SELECT id FROM exercises WHERE name='Сгибание рук с гантелями'), 5, 2, '10-12', 'normal'),
  ('33333333-3333-3333-3333-333333333333', 1, (SELECT id FROM exercises WHERE name='Планка'), 6, 3, '30-60с', 'normal');
-- День 2
INSERT INTO plan_exercises (plan_id, day_number, exercise_id, order_index, target_sets, target_reps, suggested_method) VALUES
  ('33333333-3333-3333-3333-333333333333', 2, (SELECT id FROM exercises WHERE name='Жим ногами'), 1, 3, '10-12', 'normal'),
  ('33333333-3333-3333-3333-333333333333', 2, (SELECT id FROM exercises WHERE name='Жим штанги стоя'), 2, 3, '8-10', 'normal'),
  ('33333333-3333-3333-3333-333333333333', 2, (SELECT id FROM exercises WHERE name='Негативные подтягивания'), 3, 3, '3-5', 'rest_pause'),
  ('33333333-3333-3333-3333-333333333333', 2, (SELECT id FROM exercises WHERE name='Сведение рук в кроссовере'), 4, 3, '12-15', 'normal'),
  ('33333333-3333-3333-3333-333333333333', 2, (SELECT id FROM exercises WHERE name='Разгибание на трицепс'), 5, 2, '10-12', 'normal'),
  ('33333333-3333-3333-3333-333333333333', 2, (SELECT id FROM exercises WHERE name='Скручивания на пресс'), 6, 3, '15-20', 'normal');
-- День 3
INSERT INTO plan_exercises (plan_id, day_number, exercise_id, order_index, target_sets, target_reps, suggested_method) VALUES
  ('33333333-3333-3333-3333-333333333333', 3, (SELECT id FROM exercises WHERE name='Румынская тяга'), 1, 3, '8-10', 'normal'),
  ('33333333-3333-3333-3333-333333333333', 3, (SELECT id FROM exercises WHERE name='Жим гантелей на наклонной'), 2, 3, '8-10', 'normal'),
  ('33333333-3333-3333-3333-333333333333', 3, (SELECT id FROM exercises WHERE name='Тяга верхнего блока'), 3, 3, '10-12', 'normal'),
  ('33333333-3333-3333-3333-333333333333', 3, (SELECT id FROM exercises WHERE name='Болгарские сплит-приседы'), 4, 3, '10-12', 'pyramid'),
  ('33333333-3333-3333-3333-333333333333', 3, (SELECT id FROM exercises WHERE name='Сгибание ног лёжа'), 5, 3, '10-12', 'normal');

-- Plan exercises: Upper/Lower Split (3 дня: Низ1 / Верх / Низ2)
-- День 1 Низ
INSERT INTO plan_exercises (plan_id, day_number, exercise_id, order_index, target_sets, target_reps, suggested_method) VALUES
  ('44444444-4444-4444-4444-444444444444', 1, (SELECT id FROM exercises WHERE name='Ягодичный мостик'), 1, 4, '8-12', 'normal'),
  ('44444444-4444-4444-4444-444444444444', 1, (SELECT id FROM exercises WHERE name='Румынская тяга'), 2, 3, '10-12', 'normal'),
  ('44444444-4444-4444-4444-444444444444', 1, (SELECT id FROM exercises WHERE name='Болгарские сплит-приседы'), 3, 3, '10-12', 'normal'),
  ('44444444-4444-4444-4444-444444444444', 1, (SELECT id FROM exercises WHERE name='Жим ногами'), 4, 3, '12-15', 'normal'),
  ('44444444-4444-4444-4444-444444444444', 1, (SELECT id FROM exercises WHERE name='Сгибание ног лёжа'), 5, 3, '10-12', 'normal'),
  ('44444444-4444-4444-4444-444444444444', 1, (SELECT id FROM exercises WHERE name='Гиперэкстензия'), 6, 3, '12-15', 'normal');
-- День 2 Верх
INSERT INTO plan_exercises (plan_id, day_number, exercise_id, order_index, target_sets, target_reps, suggested_method) VALUES
  ('44444444-4444-4444-4444-444444444444', 2, (SELECT id FROM exercises WHERE name='Жим гантелей на наклонной'), 1, 3, '10-12', 'normal'),
  ('44444444-4444-4444-4444-444444444444', 2, (SELECT id FROM exercises WHERE name='Тяга верхнего блока'), 2, 3, '10-12', 'normal'),
  ('44444444-4444-4444-4444-444444444444', 2, (SELECT id FROM exercises WHERE name='Жим штанги стоя'), 3, 3, '10-12', 'normal'),
  ('44444444-4444-4444-4444-444444444444', 2, (SELECT id FROM exercises WHERE name='Сведение рук в кроссовере'), 4, 3, '12-15', 'normal'),
  ('44444444-4444-4444-4444-444444444444', 2, (SELECT id FROM exercises WHERE name='Махи гантелей в стороны'), 5, 3, '12-15', 'normal'),
  ('44444444-4444-4444-4444-444444444444', 2, (SELECT id FROM exercises WHERE name='Планка'), 6, 3, '30-45с', 'normal');
-- День 3 Низ2
INSERT INTO plan_exercises (plan_id, day_number, exercise_id, order_index, target_sets, target_reps, suggested_method) VALUES
  ('44444444-4444-4444-4444-444444444444', 3, (SELECT id FROM exercises WHERE name='Ягодичный мостик'), 1, 4, '10-12', 'pyramid'),
  ('44444444-4444-4444-4444-444444444444', 3, (SELECT id FROM exercises WHERE name='Присед со штангой'), 2, 3, '8-10', 'normal'),
  ('44444444-4444-4444-4444-444444444444', 3, (SELECT id FROM exercises WHERE name='Болгарские сплит-приседы'), 3, 3, '10-12', 'normal'),
  ('44444444-4444-4444-4444-444444444444', 3, (SELECT id FROM exercises WHERE name='Жим ногами'), 4, 3, '10-12', 'normal'),
  ('44444444-4444-4444-4444-444444444444', 3, (SELECT id FROM exercises WHERE name='Сгибание ног лёжа'), 5, 3, '10-12', 'drop_set');
