"""Alembic environment configuration for database migrations.

This module configures the Alembic environment for running database migrations,
including both online and offline modes. It sets up the SQLAlchemy connection
and configures the migration context with the application's metadata.
"""
from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from ring.alembic.alembic_helpers import (
    cockroach_compare_type,
    include_object,
)
from ring.fastapp.config import get_config
from ring.models import *  # noqa: F403
from ring.sqlalchemy_base import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
config.set_main_option("sqlalchemy.url", get_config().cockroach_database_uri)
# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

import logging

logging.getLogger("alembic").setLevel(logging.DEBUG)

# add your model's MetaData object here
# for 'autogenerate' support
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
        compare_type=cockroach_compare_type,
        include_object=include_object,
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
            connection=connection,
            target_metadata=target_metadata,
            compare_type=cockroach_compare_type,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
