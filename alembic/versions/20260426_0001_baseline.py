"""Baseline revision (no-op).

Tables are still materialized at application startup via SQLAlchemy
`create_tables()` for backward compatibility. Use autogenerate for
subsequent schema changes.

Revision ID: 20260426_0001
Revises:
Create Date: 2026-04-26

"""

from typing import Sequence, Union

revision: str = "20260426_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
