"""make invite.ott non-null

Revision ID: 84618d011254
Revises: 07ff6f6066f4
Create Date: 2024-10-27 02:24:25.575582

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "84618d011254"
down_revision: Union[str, None] = "07ff6f6066f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DELETE FROM invite WHERE one_time_token_id IS NULL")
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "invite",
        "one_time_token_id",
        existing_type=sa.INTEGER(),
        nullable=False,
    )
    op.alter_column(
        "invite", "token", existing_type=sa.String(), nullable=True
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "invite",
        "one_time_token_id",
        existing_type=sa.INTEGER(),
        nullable=True,
    )
    op.alter_column(
        "invite", "token", existing_type=sa.String(), nullable=False
    )
    # ### end Alembic commands ###
