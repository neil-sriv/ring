from __future__ import annotations

from pathlib import Path
from typing import Any

import click

from dev_util.compose import compose_exec
from dev_util.dev import ROOT_DIR, dev_command, dev_group, subprocess_run
from dev_util.schema_drift import clean_dump, compare

# Prod DB is CockroachDB Cloud (cluster ring-db), not RDS. See docs/infrastructure.md.
LOCAL_COCKROACH_URI = "postgresql://root@127.0.0.1:26257/ring"
SCHEMA_SQL_PATH = Path(ROOT_DIR) / "ring" / "db" / "schema.sql"
TEST_COCKROACH_CONTAINER = "ring-test-cockroach"
# Credentials come from compose.test.yml; this cluster is ephemeral CI state.
TEST_COCKROACH_URL = (
    "postgresql://ringcockroach:ringcockroach@localhost:26257/test"
    "?sslmode=require"
)
COCKROACH_CONNECTION_STRING = (
    f"{LOCAL_COCKROACH_URI}"
    "?sslcert=%2Froot%2F.cockroach-certs%2Fclient.root.crt"
    "&sslkey=%2Froot%2F.cockroach-certs%2Fclient.root.key"
    "&sslmode=verify-full"
    "&sslrootcert=%2Froot%2F.cockroach-certs%2Fca.crt"
)


@dev_group("db")
@click.pass_context
def db(ctx: click.Context) -> None:
    pass


@compose_exec(
    "cockroach", db, service="cockroach", opts=["-it"], directory=None
)
def db_cockroach(
    ctx: click.Context,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    """
    Open an interactive CockroachDB SQL shell against the local database.
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


@compose_exec(
    "check-migrations",
    db,
    service="test-runner",
    directory="ring",
    profile="test",
    cmd="run",
    opts=["--rm"],
)
def db_check_migrations(
    ctx: click.Context,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    """Apply every migration to the empty test database.

    Guards auto-deploy: prod migrations run unattended, but the test suite
    builds its schema from db/schema.sql, so nothing else exercises the
    revision chain.
    """
    return ["alembic", "upgrade", "head"]


@dev_command("check-schema-drift", db)
def db_check_schema_drift(
    ctx: click.Context,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> None:
    """Compare db/schema.sql with the migrated test database.

    Run after `ring db check-migrations`, against the same container.
    """
    dump = subprocess_run(
        [
            "docker",
            "exec",
            TEST_COCKROACH_CONTAINER,
            "./cockroach",
            "sql",
            "--url",
            TEST_COCKROACH_URL,
            "-e",
            "SHOW CREATE ALL TABLES",
        ],
        capture_output=True,
    ).stdout

    drift = compare(clean_dump(dump), SCHEMA_SQL_PATH.read_text())
    if drift:
        raise click.ClickException(
            "db/schema.sql does not match the migrated schema:\n"
            f"{drift.report()}\n\n"
            "Apply the migration to your dev database, then run "
            "`ring db autogenerate-schema` and commit db/schema.sql."
        )
    click.echo("db/schema.sql matches the migrated schema.")


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
