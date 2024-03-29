import click
from dev_util.compose import compose_run
from dev_util.dev import cmd_run, dev_group
import os


LOCAL_POSTGRES_URI = "postgresql://ring-postgres:ring-postgres@localhost:8004/ring"


@dev_group("db")
@click.pass_context
def db(ctx: click.Context) -> None:
    pass


@cmd_run("pgcli", db)
def db_pgcli() -> list[str]:
    os.getenv("")
    return ["pgcli", LOCAL_POSTGRES_URI]


@compose_run("upgrade", db)
def db_upgrade() -> list[str]:
    return ["exec", "-w", "/src/ring", "api", "alembic", "upgrade", "head"]
