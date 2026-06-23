"""make text_embedding_768 nullable

Revision ID: 45bf29f5dbb8
Revises: 9f2f7995f154
Create Date: 2026-06-23 06:54:05.636391

"""

from __future__ import annotations

from typing import Sequence, Union

import pgvector
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "45bf29f5dbb8"
down_revision: Union[str, None] = "9f2f7995f154"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade the database to this migration version.

    Implements the forward migration by applying schema changes and data
    transformations to reach this version from the previous version.

    Raises:
        sqlalchemy.exc.SQLAlchemyError: If the migration fails
        alembic.util.CommandError: If the migration configuration is invalid
    """
    # Autogenerate could not introspect the VECTOR type and emitted sa.NullType(),
    # which does not exist in SQLAlchemy 2.x. Use the pgvector type from the
    # migration that originally added this column (0852b676e883).
    op.alter_column(
        "hybrid_search_document",
        "text_embedding_768",
        existing_type=pgvector.sqlalchemy.vector.VECTOR(dim=768),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade the database from this migration version.

    Implements the reverse migration by reverting schema changes and data
    transformations to return to the previous version.

    Raises:
        sqlalchemy.exc.SQLAlchemyError: If the migration fails
        alembic.util.CommandError: If the migration configuration is invalid
    """
    op.alter_column(
        "hybrid_search_document",
        "text_embedding_768",
        existing_type=pgvector.sqlalchemy.vector.VECTOR(dim=768),
        nullable=False,
    )
