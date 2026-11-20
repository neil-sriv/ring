"""add question added_late

Revision ID: b2d0ec9a1b64
Revises: 573c694e495e
Create Date: 2026-11-20 05:46:34.416278

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2d0ec9a1b64"
down_revision: Union[str, None] = "573c694e495e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add question.added_late, backfilling existing rows as false."""
    op.add_column(
        "question",
        sa.Column(
            "added_late",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Remove question.added_late."""
    op.drop_column("question", "added_late")
