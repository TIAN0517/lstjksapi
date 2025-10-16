# Repository Guidelines

## Project Structure & Module Organization
- `app/` contains all FastAPI and Flask back-end code; APIs live under `app/api/`, shared logic under `app/services/`, and persistence models under `app/models/`.
- `web/` holds the Flask front-end templates and static assets; `web/templates/login.html` and `web/static/js/apiClient.js` drive auth flows.
- `tests/` includes pytest suites for API, auth, and credits modules; keep new fixtures in `tests/conftest.py`.
- Supporting assets and scripts sit in `scripts/`, `deploy/`, and root shell helpers (`start_all.sh`, `check_services.sh`). Data artifacts persist in `data/`.

## Build, Test, and Development Commands
- `docker compose up -d --build` — rebuilds images and launches Postgres, Redis, API (Uvicorn), and web tier (Flask SocketIO) with health checks.
- `./start_all.sh` — local all-in-one startup: prepares venv, installs deps, brings up databases, API, web UI, Celery, and bots.
- `uvicorn app.api.main:app --host 0.0.0.0 --port 28001` & `python run_web.py` — run API and Flask UI directly during iterative debugging.
- `pytest -v` or `pytest tests/test_api_endpoints.py` — execute unit/integration suites; append `--cov=app` for coverage reports.

## Coding Style & Naming Conventions
- Python code uses 4-space indentation, snake_case for modules/functions, PascalCase for SQLAlchemy models, and SCREAMING_SNAKE_CASE for settings.
- Run `black .` and `flake8` before commits; both are declared in `requirements.txt`.
- Front-end JS follows camelCase functions, with shared helpers exported from `web/static/js/*.js`.

## Testing Guidelines
- Pytest with fixtures (`test_client`, `auth_headers`) is the standard; mark longer scenarios with `@pytest.mark.integration`.
- Aim for ≥40% project-wide coverage and ≥60% on core APIs (`app/api/`) per `tests/README.md`.
- Name files `test_*.py`, classes `Test*`, and methods `test_*`; keep deterministic data in `tests/data/` if needed.

## Commit & Pull Request Guidelines
- Follow conventional prefixes observed in history (`feat:`, `fix:`, `docs:`, `chore:`). Summaries stay under ~72 characters and describe impact, e.g., `fix: tighten TRC20 validation`.
- Reference related issues or checklists in the body; include `BREAKING` notes when APIs change.
- Pull requests should link to tracking tickets, describe testing (commands run + results), and attach screenshots for UI updates.

## Security & Configuration Tips
- Copy `.env.example` to `.env` and populate secret keys, database, Redis, Gemini, Google credentials before starting services.
- Sensitive files (`credentials/`, `data/*.db`) must never be committed; verify `.gitignore` catches new secrets.
- Regenerate API tokens and JWT secrets when rotating environments; update downstream consumers accordingly.
