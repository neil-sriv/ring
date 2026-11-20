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
    """Record late-question email sends and who already received each one."""
    op.add_column(
        "letter",
        sa.Column(
            "last_late_question_email_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.create_table(
        "late_question_email_receipt",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("letter_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["letter_id"],
            ["letter.id"],
            name="late_question_email_receipt_letter_id_fkey",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name="late_question_email_receipt_user_id_fkey",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["question.id"],
            name="late_question_email_receipt_question_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "letter_id",
            "user_id",
            "question_id",
            name="uq_late_question_email_receipt",
        ),
    )


def downgrade() -> None:
    """Remove late-question email receipts and the letter watermark."""
    op.drop_table("late_question_email_receipt")
    op.drop_column("letter", "last_late_question_email_at")
