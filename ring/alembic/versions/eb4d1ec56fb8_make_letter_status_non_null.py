"""make letter.status non-null

Revision ID: eb4d1ec56fb8
Revises: e33eb3e58a8a
Create Date: 2024-06-22 07:50:23.576232

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "eb4d1ec56fb8"
down_revision: Union[str, None] = "e33eb3e58a8a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    session = sa.orm.Session(bind=op.get_bind())
    session.execute(
        sa.text("UPDATE letter SET status = 'SENT' WHERE status IS NULL")
    )
    op.alter_column(
        "letter", "status", existing_type=sa.VARCHAR(), nullable=False
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "letter", "status", existing_type=sa.VARCHAR(), nullable=True
    )
    session = sa.orm.Session(bind=op.get_bind())
    session.execute(sa.text("UPDATE letter SET status = null"))
    # ### end Alembic commands ###
