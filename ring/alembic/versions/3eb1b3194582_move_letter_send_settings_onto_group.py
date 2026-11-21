"""move letter send settings onto group

Revision ID: 3eb1b3194582
Revises: 14d6734a0f6a
Create Date: 2026-11-21 19:13:08.334564

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from ring.alembic.backfill_letter_send_settings import (
    copy_letter_send_settings,
    restore_letter_send_settings,
)

# revision identifiers, used by Alembic.
revision: str = "3eb1b3194582"
down_revision: Union[str, None] = "14d6734a0f6a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add letter-send columns and copy them out of the group store."""
    op.add_column(
        "group",
        sa.Column("min_responder_ratio", sa.Float(), nullable=True),
    )
    op.add_column(
        "group",
        sa.Column("min_responders", sa.Integer(), nullable=True),
    )
    copy_letter_send_settings(op.get_bind())


def downgrade() -> None:
    """Put letter-send values back in the store and drop the columns."""
    restore_letter_send_settings(op.get_bind())
    op.drop_column("group", "min_responders")
    op.drop_column("group", "min_responder_ratio")
