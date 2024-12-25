from typing import Any

import click

from dev_util.compose import compose_exec
from dev_util.dev import cmd_run, dev_group

GH_ECR_URI_BASE = "ghcr.io"


@dev_group("test")
@click.pass_context
def test(ctx: click.Context) -> None:
    pass


@cmd_run("image", test)
def image(
    ctx: click.Context,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[list[str]]:
    image_tag = f"{GH_ECR_URI_BASE}/neil-sriv/ring/ring-test-runner:latest"
    return [
        [
            "docker",
            "tag",
            "ring-test-runner:latest",
            image_tag,
        ],
        [
            "docker",
            "push",
            image_tag,
        ],
    ]


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
