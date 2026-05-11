# Postgres setup

We use **PostgreSQL 16** for users, lesson progress and feedback.

## Option A — Docker (recommended, zero install)

```bash
docker compose up postgres
```
That's it. The `docker-compose.yml` already:
- Uses image `postgres:16-alpine`
- Creates user/db: `signbridge / signbridge_dev / signdb`
- Mounts `gateway/src/schema.sql` into `/docker-entrypoint-initdb.d/` so the schema runs **once** on first boot
- Persists data in the `pgdata` named volume

Connection string (already in `docker-compose.yml`):
```
postgres://signbridge:signbridge_dev@postgres:5432/signdb       # from inside docker network
postgres://signbridge:signbridge_dev@localhost:5432/signdb      # from host machine
```

## Option B — Native install on Windows

1. Download Postgres 16 from https://www.postgresql.org/download/windows/
2. During install, set the `postgres` user password (e.g. `postgres`)
3. Open SQL Shell (`psql`) and create db + user:
   ```sql
   CREATE USER signbridge WITH PASSWORD 'signbridge_dev';
   CREATE DATABASE signdb OWNER signbridge;
   ```
4. Apply the schema:
   ```bash
   psql -U signbridge -d signdb -f gateway/src/schema.sql
   ```
5. Set in `gateway/.env`:
   ```
   DATABASE_URL=postgres://signbridge:signbridge_dev@localhost:5432/signdb
   ```

## Option C — Managed (Supabase / Neon / Railway, free tier)

1. Sign up, create a Postgres project
2. Copy the connection string they give you (looks like `postgresql://USER:PASS@HOST:5432/DB`)
3. Append `?sslmode=require` if not already there
4. Set in `gateway/.env`:
   ```
   DATABASE_URL=postgresql://USER:PASS@HOST:5432/DB?sslmode=require
   DATABASE_SSL=true
   ```
5. Apply the schema once:
   ```bash
   psql "$DATABASE_URL" -f gateway/src/schema.sql
   ```

## Schema overview

| Table | Purpose |
|---|---|
| `users` | id, email, name, password_hash (bcrypt) |
| `lesson_progress` | one row per (user, lesson) — best_score, attempts, last_score |
| `feedback` | contact-form submissions (optionally linked to a user) |

Schema lives in [gateway/src/schema.sql](../gateway/src/schema.sql).

## Quick sanity check

```bash
psql "$DATABASE_URL" -c "\dt"
# Expect: feedback, lesson_progress, users

psql "$DATABASE_URL" -c "SELECT count(*) FROM users;"
# Expect: 0  (initially)
```

## Resetting (dev only)

```bash
docker compose down -v   # drops the pgdata volume
docker compose up -d postgres
```
