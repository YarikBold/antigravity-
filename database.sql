-- Удаление старых таблиц для чистого запуска
DROP TABLE IF EXISTS workout_logs CASCADE;
DROP TABLE IF EXISTS plan_exercises CASCADE;
DROP TABLE IF EXISTS exercises CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS workout_plans CASCADE;

-- ============================================================
-- Antigravity — AI Strength Training Tracker
-- Supabase (PostgreSQL) Schema + Seed Data
-- ============================================================

CREATE TABLE IF NOT EXISTS workout_plans (
  id          SERIAL PRIMARY KEY,
  name        TEXT NOT NULL,
  description TEXT,
  tags        TEXT[]
);

CREATE TABLE IF NOT EXISTS users (
  id              SERIAL PRIMARY KEY,
  name            TEXT NOT NULL,
  goal            TEXT,
  current_plan_id INTEGER REFERENCES workout_plans(id),
  schedule        INTEGER[] DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS exercises (
  id               SERIAL PRIMARY KEY,
  name             TEXT NOT NULL,
  target_muscle    TEXT NOT NULL,
  movement_pattern TEXT NOT NULL,
  media_url        TEXT
);

CREATE TABLE IF NOT EXISTS plan_exercises (
  id          SERIAL PRIMARY KEY,
  plan_id     INTEGER NOT NULL REFERENCES workout_plans(id) ON DELETE CASCADE,
  exercise_id INTEGER NOT NULL REFERENCES exercises(id)     ON DELETE CASCADE,
  day_number  INTEGER NOT NULL,
  sets        INTEGER NOT NULL DEFAULT 3,
  reps_target TEXT    NOT NULL DEFAULT '8-12'
);

CREATE TABLE IF NOT EXISTS workout_logs (
  id          SERIAL PRIMARY KEY,
  user_id     INTEGER     NOT NULL REFERENCES users(id)     ON DELETE CASCADE,
  exercise_id INTEGER     NOT NULL REFERENCES exercises(id)  ON DELETE CASCADE,
  weight      REAL        NOT NULL DEFAULT 0,
  reps        INTEGER     NOT NULL DEFAULT 0,
  rir         INTEGER     NOT NULL DEFAULT 2,
  date        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_logs_user_date     ON workout_logs(user_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_logs_user_exercise  ON workout_logs(user_id, exercise_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_plan_ex_plan_day    ON plan_exercises(plan_id, day_number);

-- SEED: PLANS
INSERT INTO workout_plans (id, name, description, tags) VALUES
  (1, 'Reboot',         'Full Body — 3 дня в неделю. Для возвращения к тренировкам и сброса веса.', ARRAY['full-body','beginner','weight-loss']),
  (2, 'Shape',           'Сплит Низ / Верх — 4 дня. Акцент на ягодицы, ноги и грудь.',              ARRAY['lower-upper','female','toning']),
  (3, 'Push-Pull-Legs',  'Классический PPL — 3 дня. Для опытных атлетов.',                          ARRAY['ppl','intermediate','hypertrophy']);

-- SEED: 15 EXERCISES
INSERT INTO exercises (id, name, target_muscle, movement_pattern, media_url) VALUES
  (1,  'Присед со штангой',           'quads',      'compound',  NULL),
  (2,  'Жим штанги лёжа',             'chest',      'compound',  NULL),
  (3,  'Тяга верхнего блока',         'back',       'compound',  NULL),
  (4,  'Жим штанги стоя',             'shoulders',  'compound',  NULL),
  (5,  'Тяга штанги в наклоне',       'back',       'compound',  NULL),
  (6,  'Румынская тяга',              'hamstrings', 'compound',  NULL),
  (7,  'Ягодичный мостик',            'glutes',     'compound',  NULL),
  (8,  'Жим гантелей на наклонной',   'chest',      'compound',  NULL),
  (9,  'Жим ногами',                  'quads',      'compound',  NULL),
  (10, 'Сведение рук в кроссовере',   'chest',      'isolation', NULL),
  (11, 'Махи гантелей в стороны',     'shoulders',  'isolation', NULL),
  (12, 'Сгибание рук с гантелями',    'biceps',     'isolation', NULL),
  (13, 'Разгибание на трицепс',       'triceps',    'isolation', NULL),
  (14, 'Сгибание ног лёжа',           'hamstrings', 'isolation', NULL),
  (15, 'Болгарские сплит-приседы',     'glutes',     'compound',  NULL),
  (16, 'Негативные подтягивания',      'back',       'compound',  NULL),
  (17, 'Австралийские подтягивания',   'back',       'compound',  NULL),
  (18, 'Подтягивания с эспандером',    'back',       'compound',  NULL);

-- SEED: PLAN Reboot (Full Body x 3)
INSERT INTO plan_exercises (plan_id, exercise_id, day_number, sets, reps_target) VALUES
  (1,1,1,3,'8-10'),(1,2,1,3,'8-10'),(1,17,1,3,'8-10'),(1,11,1,3,'12-15'),(1,12,1,2,'10-12'),
  (1,9,2,3,'10-12'),(1,4,2,3,'8-10'),(1,16,2,3,'3-5'),(1,10,2,3,'12-15'),(1,13,2,2,'10-12'),
  (1,1,3,3,'8-10'),(1,2,3,3,'8-10'),(1,18,3,3,'6-8'),(1,14,3,3,'10-12'),(1,11,3,3,'12-15');

-- SEED: PLAN Shape (Lower/Upper x 4)
INSERT INTO plan_exercises (plan_id, exercise_id, day_number, sets, reps_target) VALUES
  (2,7,1,4,'8-12'),(2,6,1,3,'10-12'),(2,15,1,3,'10-12'),(2,9,1,3,'12-15'),(2,14,1,3,'10-12'),
  (2,8,2,3,'10-12'),(2,3,2,3,'10-12'),(2,4,2,3,'10-12'),(2,10,2,3,'12-15'),(2,11,2,3,'12-15'),
  (2,7,3,4,'10-12'),(2,6,3,3,'10-12'),(2,9,3,3,'10-12'),(2,15,3,3,'10-12'),(2,14,3,3,'10-12'),
  (2,2,4,3,'8-10'),(2,5,4,3,'10-12'),(2,4,4,3,'10-12'),(2,13,4,2,'12-15'),(2,12,4,2,'12-15');

-- SEED: PLAN PPL (3 days)
INSERT INTO plan_exercises (plan_id, exercise_id, day_number, sets, reps_target) VALUES
  (3,2,1,4,'6-8'),(3,4,1,3,'8-10'),(3,8,1,3,'10-12'),(3,10,1,3,'12-15'),(3,11,1,3,'12-15'),(3,13,1,3,'10-12'),
  (3,5,2,4,'6-8'),(3,3,2,3,'8-10'),(3,6,2,3,'10-12'),(3,12,2,3,'10-12'),
  (3,1,3,4,'6-8'),(3,9,3,3,'10-12'),(3,15,3,3,'10-12'),(3,14,3,3,'10-12'),(3,7,3,3,'10-12');

-- SEED: USERS
INSERT INTO users (id, name, goal, current_plan_id, schedule) VALUES
  (1, 'Ярик',  'Возврат к тренировкам, сброс веса',      1, ARRAY[1, 3, 5]),
  (2, 'Олеся', 'Тонус, акцент на ягодицы, ноги и грудь', 2, ARRAY[1, 2, 4, 5]);

SELECT setval('users_id_seq',          (SELECT MAX(id) FROM users));
SELECT setval('workout_plans_id_seq',  (SELECT MAX(id) FROM workout_plans));
SELECT setval('exercises_id_seq',      (SELECT MAX(id) FROM exercises));
SELECT setval('plan_exercises_id_seq', (SELECT MAX(id) FROM plan_exercises));

-- ОТКЛЮЧЕНИЕ RLS (чтобы API мог работать без авторизации)
ALTER TABLE workout_plans DISABLE ROW LEVEL SECURITY;
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE exercises DISABLE ROW LEVEL SECURITY;
ALTER TABLE plan_exercises DISABLE ROW LEVEL SECURITY;
ALTER TABLE workout_logs DISABLE ROW LEVEL SECURITY;
