"""add letter automatic send deferral count

Revision ID: 573c694e495e
Revises: 9fb2468cc3b2
Create Date: 2026-10-19 19:37:02.422763

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "573c694e495e"
down_revision: Union[str, None] = "9fb2468cc3b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the automatic send-deferral counter.

    Constant default 0 backfills existing rows. Old servers omit the column
    on insert and keep working while this revision is applied.
    """
    op.add_column(
        "letter",
        sa.Column(
            "automatic_send_deferral_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Remove the automatic send-deferral counter."""
    op.drop_column("letter", "automatic_send_deferral_count")
