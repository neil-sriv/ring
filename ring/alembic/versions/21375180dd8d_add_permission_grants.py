"""add permission grants

Revision ID: 21375180dd8d
Revises: 573c694e495e
Create Date: 2026-11-10 14:47:48.585569

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from ring.authz.backfill import BACKFILL_STATEMENTS

# revision identifiers, used by Alembic.
revision: str = "21375180dd8d"
down_revision: Union[str, None] = "573c694e495e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add permission grants and backfill them from current roles."""
    op.create_table(
        "permission_grant",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("subject_api_id", sa.String(), nullable=False),
        sa.Column("resource_api_id", sa.String(), nullable=False),
        sa.Column("permission", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "subject_api_id",
            "resource_api_id",
            "permission",
            name="uq_permission_grant_subject_resource_permission",
        ),
    )
    op.create_index(
        op.f("ix_permission_grant_id"),
        "permission_grant",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_permission_grant_resource_api_id"),
        "permission_grant",
        ["resource_api_id"],
        unique=False,
    )
    for statement in BACKFILL_STATEMENTS:
        op.execute(statement)


def downgrade() -> None:
    """Drop permission grants."""
    op.drop_index(
        op.f("ix_permission_grant_resource_api_id"),
        table_name="permission_grant",
    )
    op.drop_index(
        op.f("ix_permission_grant_id"),
        table_name="permission_grant",
    )
    op.drop_table("permission_grant")
