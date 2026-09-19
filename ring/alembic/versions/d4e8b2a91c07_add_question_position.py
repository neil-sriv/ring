"""add question position

Revision ID: d4e8b2a91c07
Revises: cd37cfa88894
Create Date: 2026-09-18 03:40:00.000000

Hand-written: column add plus a Cockroach UPDATE ... FROM backfill.
Regenerate with `ring db generate` if the revision id needs to match
Alembic's usual hash style.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e8b2a91c07"
down_revision: Union[str, None] = "cd37cfa88894"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add display-order position and backfill existing questions."""
    op.add_column(
        "question",
        sa.Column(
            "position",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.execute(
        """
        UPDATE question
        SET position = sub.pos
        FROM (
            SELECT
                id,
                row_number() OVER (
                    PARTITION BY letter_id
                    ORDER BY created_at ASC, id ASC
                ) - 1 AS pos
            FROM question
        ) AS sub
        WHERE question.id = sub.id
        """
    )


def downgrade() -> None:
    """Remove question.position."""
    op.drop_column("question", "position")
