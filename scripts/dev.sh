#!/usr/bin/env bash
# TalentFlow AI — native development launcher.
# Starts the FastAPI backend (auto-reload) and the Next.js dev server
# concurrently in a single terminal. Ctrl-C stops both.
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  echo "→ No .env found — creating one from .env.example (safe defaults, mock AI mode)."
  cp .env.example .env
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-3000}"

cleanup() {
  trap - EXIT INT TERM
  kill 0 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "→ API : http://localhost:${API_PORT}/docs   (interactive API docs)"
echo "→ Web : http://localhost:${WEB_PORT}        (recruiter UI)"
echo

(cd backend && uv run uvicorn app.main:app --reload --port "${API_PORT}") &
(cd frontend && NEXT_PUBLIC_API_BASE_URL="http://localhost:${API_PORT}" npm run dev -- -p "${WEB_PORT}") &

wait
