from pathlib import Path
from typing import Any

import click

from dev_util.dev import cmd_run, dev_group

SETUP_DIR = Path(__file__).resolve().parents[1]


@dev_group("setup")
@click.pass_context
def setup(ctx: click.Context) -> None:
    pass


@cmd_run("requirements", setup, cwd=SETUP_DIR)
def requirements(
    ctx: click.Context,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[list[str]]:
    return [
        ["uv", "sync", "--extra", "dev"],
        [
            "uv",
            "pip",
            "compile",
            "pyproject.toml",
            "-o",
            "ring/requirements.txt",
        ],
        ["pre-commit", "install"],
        ["ring", "fe", "install"],
    ]


@cmd_run("local-ssl", setup, cwd=SETUP_DIR)
def local_ssl(
    ctx: click.Context,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return [
        "bash",
        "dev_util/ssl.sh",
    ]
