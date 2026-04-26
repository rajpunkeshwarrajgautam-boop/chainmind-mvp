Alembic uses `app.core.config.Settings` for `DATABASE_URL`. Run from repository root with `PYTHONPATH=.` (or an activated venv that includes the project).

- **Baseline revision** is intentionally empty: tables are still created at API startup via `create_tables()` for compatibility.
- **New changes:** prefer `alembic revision --autogenerate` against a throwaway DB that matches your models, then review and apply.
