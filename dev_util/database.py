from __future__ import annotations

import os
from typing import Any

import click

from dev_util.compose import compose_cmd_run, compose_exec
from dev_util.dev import cmd_run, dev_command, dev_group

LOCAL_POSTGRES_URI = (
    "postgresql://ring-postgres:ring-postgres@localhost:8004/ring"
)
# Prod DB is CockroachDB Cloud (cluster ring-db), not RDS. See docs/infrastructure.md.
LOCAL_COCKROACH_URI = "postgresql://root@127.0.0.1:26257/ring"
COCKROACH_CERT_DIR = "/root/.cockroach-certs"
COCKROACH_CONNECTION_STRING = f"{LOCAL_COCKROACH_URI}?sslcert={COCKROACH_CERT_DIR}/client.root.crt&sslkey={COCKROACH_CERT_DIR}/client.root.key&sslmode=verify-full&sslrootcert={COCKROACH_CERT_DIR}/ca.crt"

COCKROACH_CONNECTION_STRING = "postgresql://root@127.0.0.1:26257/ring?sslcert=%2Froot%2F.cockroach-certs%2Fclient.root.crt&sslkey=%2Froot%2F.cockroach-certs%2Fclient.root.key&sslmode=verify-full&sslrootcert=%2Froot%2F.cockroach-certs%2Fca.crt"


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
    """
    Run pgcli on the local database.
    """
    os.getenv("")
    return ["pgcli", LOCAL_POSTGRES_URI]


"""
docker compose -f compose.core.yml -f compose.dev.yml --profile dev exec -it cockroach ./cockroach sql -d ring --url "postgresql://root@127.0.0.1:26257/ring?sslcert=%2Froot%2F.cockroach-certs%2Fclient.root.crt&sslkey=%2Froot%2F.cockroach-certs%2Fclient.root.key&sslmode=verify-full&sslrootcert=%2Froot%2F.cockroach-certs%2Fca.crt"
"""


# # @compose_exec("cockroach", db, "cockroach", "./cockroach", "exec", ["-it"])
# @cmd_run("cockroach", db)
# def db_cockroach(
#     ctx: click.Context,
#     *args: list[Any],
#     **kwargs: dict[Any, Any],
# ) -> list[str]:
#     """
#     Run cockroach on the local database.
#     """
#     return [
#         "docker",
#         "compose",
#         "-f",
#         "compose.core.yml",
#         "-f",
#         "compose.dev.yml",
#         "--profile",
#         "dev",
#         "exec",
#         "-it",
#         "cockroach",
#         "./cockroach",
#         "sql",
#         "-d",
#         "ring",
#         "--url",
#         COCKROACH_CONNECTION_STRING,
#     ]


# Alternative using compose_cmd_run (simpler approach):
@compose_exec(
    "cockroach", db, service="cockroach", opts=["-it"], directory=None
)
def db_cockroach_alt(
    ctx: click.Context,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    """
    Run cockroach on the local database (alternative approach).
    """
    return [
        "./cockroach",
        "sql",
        "-d",
        "ring",
        "--url",
        COCKROACH_CONNECTION_STRING,
    ]


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


@compose_exec(
    "generate-schema",
    db,
    service="cockroach",
    opts=["-it"],
    directory=None,
    capture_output=True,
)
def db_generate_schema(
    ctx: click.Context,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return [
        "./cockroach",
        "sql",
        "-d",
        "ring",
        "--url",
        COCKROACH_CONNECTION_STRING,
        "-e",
        "SHOW CREATE ALL TABLES",
    ]


@dev_command("autogenerate-schema", db)
def db_autogenerate_schema(
    ctx: click.Context,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    results = ctx.invoke(
        db_generate_schema,
    )

    # Clean up the output using temporary character approach
    cleaned_output = results[0]

    # Step 1: Convert double quotes to temporary character
    cleaned_output = cleaned_output.replace('""', "%")

    # Step 2: Remove all remaining single quotes
    cleaned_output = cleaned_output.replace('"', "")

    # Step 3: Convert temporary character back to single quotes
    cleaned_output = cleaned_output.replace("%", '"')

    # Step 4: Remove the first line that contains "create_statement"
    lines = cleaned_output.split("\n")
    if lines and "create_statement" in lines[0]:
        lines = lines[1:]  # Remove the first line
    cleaned_output = "\n".join(lines)

    with open("ring/db/schema.sql", "w") as f:
        f.write(cleaned_output)
