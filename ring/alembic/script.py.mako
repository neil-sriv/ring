"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    """Upgrade the database to this migration version.

    Implements the forward migration by applying schema changes and data
    transformations to reach this version from the previous version.

    Raises:
        sqlalchemy.exc.SQLAlchemyError: If the migration fails
        alembic.util.CommandError: If the migration configuration is invalid
    """
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Downgrade the database from this migration version.

    Implements the reverse migration by reverting schema changes and data
    transformations to return to the previous version.

    Raises:
        sqlalchemy.exc.SQLAlchemyError: If the migration fails
        alembic.util.CommandError: If the migration configuration is invalid
    """
    ${downgrades if downgrades else "pass"}
