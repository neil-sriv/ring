"""createdatmixin

Revision ID: 46d43335aaf4
Revises: ae6e47e06c23
Create Date: 2024-07-25 05:45:43.040465

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "46d43335aaf4"
down_revision: Union[str, None] = "ae6e47e06c23"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "group",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        op.f("ix_group_created_at"), "group", ["created_at"], unique=False
    )
    op.add_column(
        "letter",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        op.f("ix_letter_created_at"), "letter", ["created_at"], unique=False
    )
    op.add_column(
        "question",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        op.f("ix_question_created_at"),
        "question",
        ["created_at"],
        unique=False,
    )
    op.add_column(
        "response",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        op.f("ix_response_created_at"),
        "response",
        ["created_at"],
        unique=False,
    )
    op.add_column(
        "user",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        op.f("ix_user_created_at"), "user", ["created_at"], unique=False
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_user_created_at"), table_name="user")
    op.drop_column("user", "created_at")
    op.drop_index(op.f("ix_response_created_at"), table_name="response")
    op.drop_column("response", "created_at")
    op.drop_index(op.f("ix_question_created_at"), table_name="question")
    op.drop_column("question", "created_at")
    op.drop_index(op.f("ix_letter_created_at"), table_name="letter")
    op.drop_column("letter", "created_at")
    op.drop_index(op.f("ix_group_created_at"), table_name="group")
    op.drop_column("group", "created_at")
    # ### end Alembic commands ###
