# TalentFlow AI — developer entry points.
# Docker path : make up                       → UI at http://localhost:3000
# Native path : make setup && make seed-native && make dev

SHELL := /bin/bash
API_PORT ?= 8000
WEB_PORT ?= 3000

.DEFAULT_GOAL := help

help: ## Show available commands
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

setup: ## First-time native setup: .env + Python venv + npm install
	@cp -n .env.example .env 2>/dev/null || true
	cd backend && uv sync
	cd frontend && npm install

up: ## Build and start the full Docker stack (API + web + PostgreSQL/pgvector)
	docker compose up --build -d
	@echo ""
	@echo "TalentFlow AI is starting:"
	@echo "  UI      ->  http://localhost:$(WEB_PORT)"
	@echo "  API     ->  http://localhost:$(API_PORT)/docs"
	@echo "  Health  ->  http://localhost:$(API_PORT)/api/v1/health"

down: ## Stop the Docker stack
	docker compose down

reset: ## Stop the stack and delete database/uploads volumes (destructive)
	docker compose down -v

logs: ## Follow Docker stack logs
	docker compose logs -f

seed: ## Load synthetic demo data (Docker path; run after `make up`)
	docker compose exec api python -m app.seed

seed-native: ## Load synthetic demo data into the local/dev database
	cd backend && uv run python -m app.seed

dev: ## Native dev servers (API + web) in one terminal
	./scripts/dev.sh

test: ## Run all test suites (backend + frontend)
	$(MAKE) test-backend
	$(MAKE) test-frontend

test-backend: ## Backend test suite (pytest)
	cd backend && uv run pytest

test-frontend: ## Frontend unit tests + typecheck
	cd frontend && npm test && npm run typecheck

lint: ## Lint backend (ruff) and frontend (eslint)
	cd backend && uv run ruff check app tests
	cd frontend && npm run lint

fmt: ## Format backend code with ruff
	cd backend && uv run ruff format app tests

health: ## Print the live health report from the running API
	curl -fsS http://localhost:$(API_PORT)/api/v1/health | python3 -m json.tool

clean: ## Remove local caches/build artifacts
	rm -rf backend/.pytest_cache backend/.ruff_cache backend/data frontend/.next frontend/coverage
