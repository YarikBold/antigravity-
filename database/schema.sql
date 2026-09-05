-- Antigravity — Principal Schema (Supabase / PostgreSQL) database/schema.sql [6]
-- Включает: кардио-расширение (бывший seed_cardio.sql), таблицы жим-календаря
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

DROP TABLE IF EXISTS bench_records CASCADE;
DROP TABLE IF EXISTS bench_calendar_state CASCADE;
DROP TABLE IF EXISTS personal_records CASCADE;
DROP TABLE IF EXISTS workout_sets CASCADE;
DROP TABLE IF EXISTS workout_logs CASCADE;
DROP TABLE IF EXISTS readiness_logs CASCADE;
DROP TABLE IF EXISTS plan_exercises CASCADE;
DROP TABLE IF EXISTS exercises CASCADE;
DROP TABLE IF EXISTS workout_plans CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 1. users — 2 хардкод-профиля, UUID PK
CREATE TABLE users (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name            TEXT NOT NULL,
  gender          TEXT NOT NULL CHECK (gender IN ('male','female')),
  goal            TEXT NOT NULL,
  current_weight  NUMERIC(5,2),
  target_weight   NUMERIC(5,2),
  current_plan_id UUID,  -- FK не ставим: циклическая ссылка с workout_plans
  schedule        INT[] NOT NULL DEFAULT '{1,3,5}',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. workout_plans
CREATE TABLE workout_plans (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name            TEXT NOT NULL,
  target_user_id  UUID REFERENCES users(id) ON DELETE SET NULL,
  split_type      TEXT NOT NULL CHECK (split_type IN ('full_body','upper_lower','ppl','custom')),
  description     TEXT
);

-- 3. exercises — биомеханика (+cardio/conditioning для гибридного кардио)
CREATE TABLE exercises (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name              TEXT NOT NULL UNIQUE,
  target_muscle     TEXT NOT NULL,
  synergists        TEXT[] NOT NULL DEFAULT '{}',
  movement_pattern  TEXT NOT NULL CHECK (movement_pattern IN (
                      'horizontal_push','vertical_push','horizontal_pull','vertical_pull',
                      'squat','hinge','lunge','isolation','core','cardio','conditioning')),
  equipment         TEXT NOT NULL DEFAULT 'barbell',
  mechanics         TEXT NOT NULL CHECK (mechanics IN ('compound','isolation')),
  joint_stress      TEXT[] NOT NULL DEFAULT '{}',
  cns_load          INT NOT NULL CHECK (cns_load BETWEEN 1 AND 5),
  media_url         TEXT
);

-- 4. plan_exercises
CREATE TABLE plan_exercises (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id           UUID NOT NULL REFERENCES workout_plans(id) ON DELETE CASCADE,
  day_number        INT NOT NULL CHECK (day_number BETWEEN 1 AND 7),
  exercise_id       UUID NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
  order_index       INT NOT NULL DEFAULT 1,
  target_sets       INT NOT NULL DEFAULT 3 CHECK (target_sets BETWEEN 1 AND 10),
  target_reps       TEXT NOT NULL DEFAULT '8-12',
  suggested_method  TEXT NOT NULL DEFAULT 'normal' CHECK (suggested_method IN ('normal','drop_set','rest_pause','pyramid','amrap','emom')),
  UNIQUE(plan_id, day_number, exercise_id)
);

-- 5. readiness_logs
CREATE TABLE readiness_logs (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  date            DATE NOT NULL DEFAULT CURRENT_DATE,
  sleep_quality   INT NOT NULL CHECK (sleep_quality BETWEEN 1 AND 5),
  stress_level    INT NOT NULL CHECK (stress_level BETWEEN 1 AND 5),
  soreness_areas  TEXT[] NOT NULL DEFAULT '{}',
  cns_fatigue     INT NOT NULL CHECK (cns_fatigue BETWEEN 1 AND 5),
  readiness_score NUMERIC(3,2),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(user_id, date)
);

-- 6. workout_logs (+кардио-метаданные сессии)
CREATE TABLE workout_logs (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  plan_id                 UUID REFERENCES workout_plans(id) ON DELETE SET NULL,
  date                    DATE NOT NULL DEFAULT CURRENT_DATE,
  completed               BOOLEAN NOT NULL DEFAULT false,
  session_type            TEXT NOT NULL DEFAULT 'strength' CHECK (session_type IN ('strength','cardio')),
  total_duration_minutes  INT,
  perceived_effort_rpe    INT CHECK (perceived_effort_rpe BETWEEN 1 AND 10),
  notes                   TEXT,
  created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7. workout_sets (вес/повторы nullable для кардио-сетов; + duration/rounds, + emom)
CREATE TABLE workout_sets (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  log_id            UUID NOT NULL REFERENCES workout_logs(id) ON DELETE CASCADE,
  exercise_id       UUID NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
  set_number        INT NOT NULL CHECK (set_number BETWEEN 1 AND 20),
  set_type          TEXT NOT NULL DEFAULT 'normal' CHECK (set_type IN ('normal','drop_set','rest_pause','pyramid','emom')),
  weight            NUMERIC(6,2) DEFAULT NULL,
  reps              INT DEFAULT NULL CHECK (reps IS NULL OR reps >= 0),
  rir               INT NOT NULL DEFAULT 2 CHECK (rir BETWEEN 0 AND 5),
  duration_seconds  INT,
  completed_rounds  INT
);

-- 8. personal_records — e1RM PR tracker
CREATE TABLE personal_records (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  exercise_id UUID NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
  e1rm        NUMERIC(6,2) NOT NULL,
  weight      NUMERIC(6,2) NOT NULL,
  reps        INT NOT NULL,
  date        DATE NOT NULL DEFAULT CURRENT_DATE,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(user_id, exercise_id)
);

-- 9. bench_calendar_state — база 1ПМ жим-календаря (серверная копия localStorage)
CREATE TABLE bench_calendar_state (
  user_id   UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  base_1rm  NUMERIC(5,2) NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 10. bench_records — факты жимовых дней (Пн/Чт) + AMRAP
CREATE TABLE bench_records (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  date            DATE NOT NULL,
  day_type        TEXT NOT NULL DEFAULT 'heavy' CHECK (day_type IN ('heavy','volume')),
  planned_weight  NUMERIC(6,2),
  actual_weight   NUMERIC(6,2),
  reps            INT,
  sets_done       INT,
  amrap_reps      INT,
  notes           TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(user_id, date)
);

-- Indexes
CREATE INDEX idx_plan_ex_plan_day ON plan_exercises(plan_id, day_number, order_index);
CREATE INDEX idx_logs_user_date ON workout_logs(user_id, date DESC);
CREATE INDEX idx_sets_log_ex ON workout_sets(log_id, exercise_id);
CREATE INDEX idx_readiness_user_date ON readiness_logs(user_id, date DESC);
CREATE INDEX idx_ex_muscle ON exercises(target_muscle);
CREATE INDEX idx_pr_user_ex ON personal_records(user_id, exercise_id);
CREATE INDEX idx_bench_records_user_date ON bench_records(user_id, date DESC);

-- RLS disabled for MVP (2 профиля без auth)
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE workout_plans DISABLE ROW LEVEL SECURITY;
ALTER TABLE exercises DISABLE ROW LEVEL SECURITY;
ALTER TABLE plan_exercises DISABLE ROW LEVEL SECURITY;
ALTER TABLE readiness_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE workout_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE workout_sets DISABLE ROW LEVEL SECURITY;
ALTER TABLE personal_records DISABLE ROW LEVEL SECURITY;
ALTER TABLE bench_calendar_state DISABLE ROW LEVEL SECURITY;
ALTER TABLE bench_records DISABLE ROW LEVEL SECURITY;

-- ============================================================
-- ИНКРЕМЕНТАЛЬНАЯ МИГРАЦИЯ для существующей БД (пропустить на чистой установке)
-- ============================================================
-- ALTER TABLE exercises DROP CONSTRAINT IF EXISTS exercises_movement_pattern_check;
-- ALTER TABLE exercises ADD CONSTRAINT exercises_movement_pattern_check
--   CHECK (movement_pattern IN ('horizontal_push','vertical_push','horizontal_pull','vertical_pull',
--     'squat','hinge','lunge','isolation','core','cardio','conditioning'));
-- ALTER TABLE workout_sets ALTER COLUMN weight DROP NOT NULL;
-- ALTER TABLE workout_sets ALTER COLUMN weight SET DEFAULT NULL;
-- ALTER TABLE workout_sets ALTER COLUMN reps DROP NOT NULL;
-- ALTER TABLE workout_sets ALTER COLUMN reps SET DEFAULT NULL;
-- ALTER TABLE workout_sets ADD COLUMN IF NOT EXISTS duration_seconds INT;
-- ALTER TABLE workout_sets ADD COLUMN IF NOT EXISTS completed_rounds INT;
-- ALTER TABLE workout_sets DROP CONSTRAINT IF EXISTS workout_sets_set_type_check;
-- ALTER TABLE workout_sets ADD CONSTRAINT workout_sets_set_type_check
--   CHECK (set_type IN ('normal','drop_set','rest_pause','pyramid','emom'));
-- ALTER TABLE workout_logs ADD COLUMN IF NOT EXISTS session_type TEXT NOT NULL DEFAULT 'strength';
-- ALTER TABLE workout_logs ADD COLUMN IF NOT EXISTS total_duration_minutes INT;
-- ALTER TABLE workout_logs ADD COLUMN IF NOT EXISTS perceived_effort_rpe INT;
-- ALTER TABLE workout_logs ADD COLUMN IF NOT EXISTS notes TEXT;
-- (Таблицы bench_calendar_state / bench_records создаются блоками 9-10 выше.)
