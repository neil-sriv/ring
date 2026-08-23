"""remove stale letter participants

Revision ID: cd37cfa88894
Revises: b856777dd9ce
Create Date: 2026-08-23 20:29:08.597004

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cd37cfa88894"
down_revision: Union[str, None] = "b856777dd9ce"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade the database to this migration version.

    Data-only cleanup of the letter/group association tables:

    1. remove_member used to leave removed users in letter.participants,
       so they kept showing up in reply tracking, reminder emails, and
       send thresholds. Delete participants of unsent (in-progress or
       upcoming) letters who are no longer members of the letter's group.
       Sent letters keep their participants as a historical record.
    2. The add_members endpoint used to insert participants twice and
       could re-add existing members. Dedupe both association tables,
       keeping one row per pair. Neither table has an explicit primary
       key, so use CockroachDB's hidden rowid column.
    """
    op.execute(
        """
        DELETE FROM letter_to_user_assocation
        WHERE letter_id IN (
            SELECT id FROM letter
            WHERE status IN ('IN_PROGRESS', 'UPCOMING')
            AND group_id IS NOT NULL
        )
        AND NOT EXISTS (
            SELECT 1
            FROM letter
            JOIN user_group_assocation
                ON user_group_assocation.group_id = letter.group_id
            WHERE letter.id = letter_to_user_assocation.letter_id
            AND user_group_assocation.user_id
                = letter_to_user_assocation.user_id
        )
        """
    )
    op.execute(
        """
        DELETE FROM letter_to_user_assocation
        WHERE rowid NOT IN (
            SELECT min(rowid)
            FROM letter_to_user_assocation
            GROUP BY letter_id, user_id
        )
        """
    )
    op.execute(
        """
        DELETE FROM user_group_assocation
        WHERE rowid NOT IN (
            SELECT min(rowid)
            FROM user_group_assocation
            GROUP BY user_id, group_id
        )
        """
    )


def downgrade() -> None:
    """Downgrade the database from this migration version.

    The deleted stale and duplicate association rows cannot be restored,
    so this is a no-op.
    """
