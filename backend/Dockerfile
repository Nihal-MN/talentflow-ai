# TalentFlow AI — backend image (FastAPI + SQLAlchemy + Alembic).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_LINK_MODE=copy

# curl is used by the container healthcheck in docker-compose.
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv (pinned major) to resolve the committed lockfile.
RUN pip install --no-cache-dir "uv>=0.12,<0.13"

# Dependencies first for layer caching.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Application code and migrations.
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["./docker-entrypoint.sh"]
