"""add media type to image

Revision ID: 8042a30020a6
Revises: d4e29ddb3e5d
Create Date: 2024-09-18 02:49:54.409056

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8042a30020a6"
down_revision: Union[str, None] = "d4e29ddb3e5d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "image",
        sa.Column(
            "media_type", sa.String(), nullable=False, server_default="image"
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("image", "media_type")
    # ### end Alembic commands ###
