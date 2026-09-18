"""one cyclic upcoming and in-progress letter per group

Revision ID: a7c3e91f0b24
Revises: cd37cfa88894
Create Date: 2026-09-18 03:20:00.000000

Hand-written: autogenerate does not emit Cockroach partial unique
indexes. Regenerate with `ring db generate` if the revision id needs
to match Alembic's usual hash style.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a7c3e91f0b24"
down_revision: Union[str, None] = "cd37cfa88894"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add partial unique indexes for cyclic cadence status."""
    op.execute(
        """
        CREATE UNIQUE INDEX uniq_one_cyclic_upcoming_per_group
        ON letter (group_id)
        WHERE letter_type = 'CYCLIC' AND status = 'UPCOMING';
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uniq_one_cyclic_in_progress_per_group
        ON letter (group_id)
        WHERE letter_type = 'CYCLIC' AND status = 'IN_PROGRESS';
        """
    )


def downgrade() -> None:
    """Drop the cyclic cadence status indexes."""
    op.execute("DROP INDEX IF EXISTS uniq_one_cyclic_upcoming_per_group")
    op.execute("DROP INDEX IF EXISTS uniq_one_cyclic_in_progress_per_group")
