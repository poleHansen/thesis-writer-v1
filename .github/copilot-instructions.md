# Project Guidelines

## Build And Test

- Use `uv` for Python dependency management and command execution in this repo.
- Install dependencies from the repo root with `uv sync`.
- Start the API with `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir apps/api/src --reload`.
- Start the web app with `uv run python apps/web/server.py`.
- On Windows, prefer `uv run python -m pytest ...` instead of `uv run pytest ...` so tests run in the project environment instead of a globally installed `pytest`.
- Run focused tests for touched areas before finishing changes. Current test suites live in `apps/api/tests/` and `packages/methodology-engine/tests/`.

## Architecture

- This is a Python-first monorepo. `apps/` contains runnable applications, `packages/` contains reusable domain packages, `docs/architecture/` contains the canonical design docs, and `storage/` contains local development data.
- `apps/api/src/app/` is the FastAPI service. Keep route handlers thin and put business logic in `services/` and persistence logic in `repositories/`.
- Shared domain contracts and pipeline packages belong under `packages/`, not inside the API app, when logic is intended to be reused across ingestion, methodology, rendering, or export flows.
- Preserve the separation between API contract models in `apps/api/src/app/models/` and SQLAlchemy persistence models in `apps/api/src/app/db/`; do not merge request/response schemas with ORM records.
- For system design, state flow, schemas, and contracts, link to the docs in `docs/architecture/` instead of restating them in code comments or new instructions.

## Conventions

- Follow the naming and directory conventions documented in `docs/architecture/conventions.md`: lowercase underscore package names, plural API resource routes, PascalCase data models, and uppercase underscore environment variables.
- Prefer relative project-root logical paths in persisted models and artifacts; avoid baking absolute local machine paths into business data.
- When changing settings or database initialization code, keep it test-friendly. The repo already relies on deferred settings and database session setup so tests can override the database configuration safely.
- If tests need a temporary database, set `DATABASE_URL` before importing `app.main`; importing first can freeze settings and engine initialization to the default connection.
- `core_types.common.CoreModel` uses `use_enum_values=True`; in service and repository code, enum-like fields are typically plain strings already, so do not access `.value`.
- When generating new Brief, Outline, SlidePlan, Artifact, or Export records, keep the corresponding `project.latest_*_id` fields in sync so aggregate project views stay current.
- Async or generation-style endpoints should persist a `TaskRun` trail with payload, result, and status so failures remain diagnosable.

## References

- See `README.md` for local development entry points.
- See `apps/api/README.md` and `apps/web/README.md` for app-specific startup details.
- See `docs/architecture/tech-stack.md` for platform choices and intended evolution.
- See `docs/architecture/conventions.md` for naming, environment variable, logging, and commit conventions.
- See `docs/architecture/data-models.md`, `docs/architecture/database-schema.md`, `docs/architecture/api-contracts.md`, and `docs/architecture/project-state-machine.md` for the authoritative product model and lifecycle definitions.
