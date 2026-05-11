-- ──────────────────────────────────────────────────────────────
-- SignBridge — Postgres schema
-- Apply once:  psql "$DATABASE_URL" -f src/schema.sql
-- (docker-compose mounts this; it auto-runs on first container start)
-- ──────────────────────────────────────────────────────────────

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email         TEXT UNIQUE NOT NULL,
  name          TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_lower ON users (lower(email));

CREATE TABLE IF NOT EXISTS lesson_progress (
  user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
  lesson_id   TEXT NOT NULL,
  best_score  NUMERIC(5,2) NOT NULL DEFAULT 0,
  attempts    INT NOT NULL DEFAULT 0,
  last_score  NUMERIC(5,2),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, lesson_id)
);
CREATE INDEX IF NOT EXISTS idx_progress_user ON lesson_progress(user_id);

CREATE TABLE IF NOT EXISTS feedback (
  id         BIGSERIAL PRIMARY KEY,
  user_id    UUID REFERENCES users(id) ON DELETE SET NULL,
  name       TEXT,
  email      TEXT,
  category   TEXT NOT NULL DEFAULT 'general',
  message    TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback(created_at DESC);
