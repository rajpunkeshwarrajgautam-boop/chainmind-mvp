# Contributing

## Local setup

1. Python **3.12+** and Node **18.17+** (for `web/`).
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and set at least `JWT_SECRET` (32+ chars) and `DATABASE_URL` (SQLite path is fine for dev).

## Checks before opening a PR

```bash
# API
set PYTHONPATH=.
set ENVIRONMENT=test
set DATABASE_URL=sqlite:///:memory:
set JWT_SECRET=ci-jwt-secret-minimum-32-characters-long
set CELERY_TASK_ALWAYS_EAGER=true
pytest tests/ -q
python scripts/verify_vertical_slice.py --in-process
```

```bash
# Web
cd web
npm ci
npm run lint
npm run build
```

## Database migrations (Alembic)

Alembic is configured under `alembic/`. The initial revision is a **no-op**; the app still calls `create_tables()` on startup for backward compatibility.

```bash
set PYTHONPATH=.
alembic upgrade head
```

For schema changes after the baseline, use `alembic revision --autogenerate -m "..."` (with a real `DATABASE_URL` reflecting your models) and review the generated ops before merging.

## Style

Match existing formatting and imports. Keep changes focused on one concern per PR.
