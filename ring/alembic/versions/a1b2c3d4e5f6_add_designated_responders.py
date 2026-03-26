"""add designated responders tables for groups and letters

Revision ID: a1b2c3d4e5f6
Revises: 9f2f7995f154
Create Date: 2026-03-26 00:00:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "9f2f7995f154"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "group_designated_responder",
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("group.id")),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id")),
    )
    op.create_table(
        "letter_designated_responder",
        sa.Column("letter_id", sa.Integer(), sa.ForeignKey("letter.id")),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id")),
    )


def downgrade() -> None:
    op.drop_table("letter_designated_responder")
    op.drop_table("group_designated_responder")
