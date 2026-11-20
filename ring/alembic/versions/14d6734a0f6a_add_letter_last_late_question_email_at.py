"""add letter last late question email at

Revision ID: 14d6734a0f6a
Revises: b2d0ec9a1b64
Create Date: 2026-11-20 06:33:20.936123

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "14d6734a0f6a"
down_revision: Union[str, None] = "b2d0ec9a1b64"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Record when a letter last sent its batched late-question email."""
    op.add_column(
        "letter",
        sa.Column(
            "last_late_question_email_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Remove letter.last_late_question_email_at."""
    op.drop_column("letter", "last_late_question_email_at")
