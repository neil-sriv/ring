from pathlib import Path
from typing import Any

import click

from dev_util.compose import compose_exec, compose_run
from dev_util.dev import dev_group


@dev_group("test")
@click.pass_context
def test(ctx: click.Context) -> None:
    pass


@compose_exec("run", test, service="test-runner", profile="test", cmd="run")
def run(
    ctx: click.Context,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return [
        "pytest",
        "-c",
        "ring/tests/pytest.ini",
    ]


@compose_run("run-ci", test, profile="test")
def run_ci(
    ctx: click.Context,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return [
        "up",
        "--exit-code-from",
        "test-runner",
    ]


@compose_exec("server", test, service="test-runner", profile="test", cmd="run")
def server(
    ctx: click.Context,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return [
        "pytest",
        "-f",
        "-c",
        "ring/tests/pytest.ini",
        "--color=yes",
        "--code-highlight=yes",
    ]
