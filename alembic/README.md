Alembic uses `app.core.config.Settings` for `DATABASE_URL`. Run from repository root with `PYTHONPATH=.` (or an activated venv that includes the project).

- **Baseline (`20260426_0001`)** is a no-op marker revision.
- **`20260426_0002_initial_schema`** runs `Base.metadata.create_all` only when the `tenants` table is missing, so it is safe alongside API startup `create_tables()`. It does not support `alembic upgrade --sql` (offline mode).
- **New changes:** prefer `alembic revision --autogenerate` against a throwaway DB that matches your production **dialect**, then review and apply.
