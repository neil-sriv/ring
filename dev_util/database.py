import os
from typing import Any

import click

from dev_util.compose import compose_exec
from dev_util.dev import cmd_run, dev_group

LOCAL_POSTGRES_URI = (
    "postgresql://ring-postgres:ring-postgres@localhost:8004/ring"
)
PROD_POSTGRES_URI = "postgresql://ringpostgres:ringpostgres@ring-postgres.c9gw8w2m4ayu.us-east-1.rds.amazonaws.com:5432/ring"


@dev_group("db")
@click.pass_context
def db(ctx: click.Context) -> None:
    pass


@cmd_run("pgcli", db)
def db_pgcli(
    ctx: click.Context,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    os.getenv("")
    return ["pgcli", LOCAL_POSTGRES_URI]


@compose_exec("upgrade", db, "api", "ring")
def db_upgrade(
    ctx: click.Context,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return ["alembic", "upgrade", "head"]


@compose_exec("generate", db, "api", "ring")
@click.argument("message")
def db_generate(
    ctx: click.Context,
    message: str,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return ["alembic", "revision", "--autogenerate", "-m", message]


@compose_exec("alembic", db, "api", "ring")
def db_alembic(
    ctx: click.Context,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return ["alembic"]
