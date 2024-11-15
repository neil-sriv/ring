"""make response participant unique

Revision ID: c464c74a2365
Revises: eb4d1ec56fb8
Create Date: 2024-06-30 21:58:06.275281

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c464c74a2365"
down_revision: Union[str, None] = "eb4d1ec56fb8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(
        "participant_question_unique",
        "response",
        ["participant_id", "question_id"],
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        "participant_question_unique", "response", type_="unique"
    )
    # ### end Alembic commands ###
