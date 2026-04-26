"""Materialize ORM schema once when DB is empty (coexists with create_tables).

`app.main` still calls `create_tables()` on startup for MVP simplicity. If the
database already has tables (typical after first boot), this revision is a
no-op. If you run ``alembic upgrade head`` on an empty database before starting
the API, ``Base.metadata.create_all`` runs here instead.

Offline mode (``alembic upgrade --sql``) is not supported for this revision.

Revision ID: 20260426_0002
Revises: 20260426_0001
Create Date: 2026-04-21

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import context, op
from sqlalchemy import inspect

from app.db.base import Base

import app.db.models  # noqa: F401 — register tables on Base.metadata

revision: str = "20260426_0002"
down_revision: Union[str, None] = "20260426_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if context.is_offline_mode():
        raise NotImplementedError(
            "20260426_0002_initial_schema requires an online DB connection; "
            "offline SQL generation is not implemented for this revision."
        )
    bind = op.get_bind()
    if inspect(bind).has_table("tenants"):
        return
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    """Intentionally a no-op: dropping the full schema is unsafe once data exists."""
