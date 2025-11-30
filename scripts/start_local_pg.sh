#!/usr/bin/env bash
set -euo pipefail

PGDATA="${PGDATA:-./.local_pgdata}"
PGPORT="${PGPORT:-5432}"
DB_NAME="${DB_NAME:-superscooters}"
DB_USER="${DB_USER:-superscooters}"
DB_PASSWORD="${DB_PASSWORD:-superscooters}"
MIGRATIONS_PATH="${MIGRATIONS_PATH:-./migrations/001_init.sql}"

if ! command -v initdb >/dev/null 2>&1; then
  echo "initdb not found. Please install PostgreSQL (e.g. via brew install postgresql)."
  exit 1
fi

if ! command -v pg_ctl >/dev/null 2>&1; then
  echo "pg_ctl not found. Please ensure PostgreSQL bin is on PATH."
  exit 1
fi

mkdir -p "${PGDATA}"

if [ ! -s "${PGDATA}/PG_VERSION" ]; then
  echo "Initializing Postgres data directory at ${PGDATA}"
  initdb --auth=trust --username=postgres --pgdata="${PGDATA}" >/dev/null
  echo "host all all 127.0.0.1/32 trust" >> "${PGDATA}/pg_hba.conf"
  echo "host all all ::1/128 trust" >> "${PGDATA}/pg_hba.conf"
fi

# Start postgres if not running
if ! pg_ctl -D "${PGDATA}" -o "-p ${PGPORT}" status >/dev/null 2>&1; then
  echo "Starting Postgres on port ${PGPORT}"
  pg_ctl -D "${PGDATA}" -o "-p ${PGPORT}" -l "${PGDATA}/logfile" start >/dev/null
fi

psql_args=(-h 127.0.0.1 -p "${PGPORT}" -U postgres -d postgres -v "ON_ERROR_STOP=1")

create_sql=$(cat <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${DB_USER}') THEN
    CREATE ROLE ${DB_USER} LOGIN PASSWORD '${DB_PASSWORD}';
  END IF;
  IF NOT EXISTS (SELECT FROM pg_database WHERE datname = '${DB_NAME}') THEN
    CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};
  END IF;
END;
$$;
SQL
)

psql "${psql_args[@]}" -c "${create_sql}" >/dev/null

echo "Postgres is ready. DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@127.0.0.1:${PGPORT}/${DB_NAME}"
if [ -f "${MIGRATIONS_PATH}" ]; then
  echo "Applying migrations from ${MIGRATIONS_PATH}"
  psql "postgresql://${DB_USER}:${DB_PASSWORD}@127.0.0.1:${PGPORT}/${DB_NAME}" -f "${MIGRATIONS_PATH}"
else
  echo "Migration file not found at ${MIGRATIONS_PATH}, skipping"
fi
echo "To stop: pg_ctl -D ${PGDATA} stop"
