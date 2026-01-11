"""add_comment_model

Revision ID: d5e0f7995140
Revises: f3ff76cffae4
Create Date: 2025-07-27 18:23:22.280615

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d5e0f7995140"
down_revision: Union[str, None] = "f3ff76cffae4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the comment table with generic weak reference support.

    Comments can be attached to any API-identified object using the
    target_api_id field which stores the api_identifier of the target.
    """
    op.create_table(
        "comment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("api_identifier", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("target_api_id", sa.String(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_comment_api_identifier"),
        "comment",
        ["api_identifier"],
        unique=True,
    )
    op.create_index(
        op.f("ix_comment_author_id"),
        "comment",
        ["author_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_comment_created_at"),
        "comment",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_comment_id"),
        "comment",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_comment_target_api_id"),
        "comment",
        ["target_api_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the comment table."""
    op.drop_index(op.f("ix_comment_target_api_id"), table_name="comment")
    op.drop_index(op.f("ix_comment_id"), table_name="comment")
    op.drop_index(op.f("ix_comment_created_at"), table_name="comment")
    op.drop_index(op.f("ix_comment_author_id"), table_name="comment")
    op.drop_index(op.f("ix_comment_api_identifier"), table_name="comment")
    op.drop_table("comment")
