#!/bin/sh
# TalentFlow AI API entrypoint: run migrations, then serve.
# Retries migrations briefly to tolerate a database that is still warming up.
set -e

echo "→ Applying database migrations (alembic upgrade head)..."
attempts=0
until alembic upgrade head; do
  attempts=$((attempts + 1))
  if [ "$attempts" -ge 10 ]; then
    echo "✗ Migrations failed after $attempts attempts — giving up." >&2
    exit 1
  fi
  echo "…database not ready yet (attempt $attempts) — retrying in 3s"
  sleep 3
done

echo "→ Starting API on :8000"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
