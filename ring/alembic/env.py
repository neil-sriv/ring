"""Alembic environment configuration for database migrations.

This module configures the Alembic environment for running database migrations,
including both online and offline modes. It sets up the SQLAlchemy connection
and configures the migration context with the application's metadata.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from ring.config import get_config
from ring.letters.models.default_question_model import (
    DefaultQuestion,  # type: ignore # noqa: F401  # type: ignore # noqa: F401
)
from ring.letters.models.letter_model import (
    Letter,  # type: ignore # noqa: F401
)
from ring.letters.models.question_model import (
    Question,  # type: ignore # noqa: F401
)
from ring.letters.models.response_model import (
    Response,  # type: ignore # noqa: F401
)
from ring.notifications.models.subscription import (
    Subscription,  # type: ignore # noqa: F401
)
from ring.parties.models.group_key_value import (
    GroupKeyValue,  # type: ignore # noqa: F401
)
from ring.parties.models.group_model import Group  # type: ignore # noqa: F401
from ring.parties.models.invite_model import (
    Invite,  # type: ignore # noqa: F401  # type: ignore # noqa: F401
)
from ring.parties.models.one_time_token_model import (
    OneTimeToken,  # type: ignore # noqa: F401
)
from ring.parties.models.user_model import User  # type: ignore # noqa: F401
from ring.s3.models.s3_model import Image, S3File  # type: ignore # noqa: F401
from ring.sqlalchemy_base import Base
from ring.tasks.models.schedule_model import (
    Schedule,  # type: ignore # noqa: F401
)
from ring.tasks.models.task_model import Task  # type: ignore # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
config.set_main_option("sqlalchemy.url", get_config().cockroach_database_uri)
# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode without requiring a database connection.

    Configures the migration context with just a URL and executes migrations
    without requiring an actual database connection. Useful for generating
    SQL scripts that can be run later.

    Raises:
        alembic.util.CommandError: If the configuration is invalid
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with an active database connection.

    Creates a SQLAlchemy Engine instance and executes migrations using
    an active database connection. This is the default mode for running
    migrations in a development or production environment.

    Raises:
        sqlalchemy.exc.SQLAlchemyError: If database connection fails
        alembic.util.CommandError: If the configuration is invalid
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
