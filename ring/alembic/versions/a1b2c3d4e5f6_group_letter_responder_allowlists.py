"""add group and letter responder allowlist association tables

Revision ID: a1b2c3d4e5f6
Revises: 9f2f7995f154
Create Date: 2026-03-26

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "9f2f7995f154"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "group_responder_allowlist",
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["group.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("group_id", "user_id"),
    )
    op.create_table(
        "letter_responder_allowlist",
        sa.Column("letter_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["letter_id"], ["letter.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("letter_id", "user_id"),
    )


def downgrade() -> None:
    op.drop_table("letter_responder_allowlist")
    op.drop_table("group_responder_allowlist")
