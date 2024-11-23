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
config.set_main_option("sqlalchemy.url", get_config().sqlalchemy_database_uri)

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
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

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
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

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
