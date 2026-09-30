# Release Checklist

Repeat this before every release tag. Each line has the exact command or link —
nothing here is aspirational; if a step can't be done, the release waits.

## 1. Tests

- [ ] Backend, hermetic: `cd backend && uv run pytest` → expect **110 passed, 1 skipped**
- [ ] Backend, PostgreSQL+pgvector (needs `docker compose up -d db`):
      `cd backend && DATABASE_URL="postgresql+psycopg://talentflow:talentflow@localhost:5432/talentflow" uv run pytest`
      → expect **111 passed, 0 skipped**
- [ ] Frontend: `cd frontend && npm test && npm run typecheck` → expect 18 passed + clean types

## 2. Lint

- [ ] `cd backend && uv run ruff check app tests` → clean
- [ ] `cd backend && uv run ruff format --check app tests` → clean
- [ ] `cd frontend && npm run lint` → clean

## 3. Build

- [ ] `cd frontend && npm run build` → compiled, routes generated
- [ ] Docker: `docker compose build` → all images build
- [ ] Clean start (destructive): `docker compose down -v && docker compose up --build -d`
      → db + api reach **healthy**; `alembic upgrade head` runs inside `docker-entrypoint.sh`
- [ ] `docker compose exec api python -m app.seed` → demo dataset loads
- [ ] Smoke: UI on :3000 renders, `/api/v1/health` reports all-operational, `/docs` opens

## 4. Security

- [ ] Secret sweep: `git grep -nE "(sk-[A-Za-z0-9]{20,}|gh[pous]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})"` → nothing
- [ ] No new files expose PII / real candidate data (`examples/` must remain synthetic)
- [ ] `.env` remains untracked; `.env.example` holds placeholders only
- [ ] Dependabot / secret-scanning / CodeQL alerts triaged on GitHub (Security tab)

## 5. Version & changelog

- [ ] `CHANGELOG.md`: move items from `Unreleased` into a new `[x.y.z] - YYYY-MM-DD` section
- [ ] Version bump where a version string exists (backend `pyproject.toml`,
      frontend `package.json`) — SemVer: breaking = major, feature = minor, fix = patch
- [ ] Decide the number honestly: v0.x.y until the API is stable; do not jump to 1.0.0 for looks

## 6. Docs & screenshots

- [ ] README claims still true (features, commands, badges)
- [ ] Screenshots current (`docs/screenshots/`) — re-capture if any UI changed
- [ ] `docs/` updated for any behavior/contract change
- [ ] `CHATGPT_REVIEW_HANDOFF.md` refreshed if an external review will follow the release

## 7. Tag & release (GitHub)

- [ ] Merge everything to `main`; CI green on the final commit
- [ ] Tag: `git tag -a vx.y.z -m "vx.y.z"` then `git push origin vx.y.z`
- [ ] GitHub Release: `gh release create vx.y.z --title "vx.y.z" --notes-file <notes.md>`
      (or Releases → Draft a new release → pick the tag)
- [ ] Release notes include: overview, highlights, quick start, known limitations,
      Responsible AI statement (template: the v0.1.0 release notes)
- [ ] Verify the release page renders; links work

## 8. After

- [ ] Announce where appropriate (LinkedIn, etc.) — describing only what's verified
- [ ] Open issues for anything deferred during the release
- [ ] Close the milestone (if using one)
