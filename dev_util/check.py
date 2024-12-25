from typing import Any

import click

from dev_util.dev import cmd_run, dev_group


@dev_group("check")
@click.pass_context
def check(ctx: click.Context) -> None:
    pass


@cmd_run("lint", check)
@click.option("--fix", is_flag=True, default=False)
def lint(
    ctx: click.Context,
    fix: bool,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[list[str]]:
    return [
        [
            "uv",
            "run",
            "ruff",
            "format",
        ]
        + ([] if fix else ["--diff"]),
        [
            "uv",
            "run",
            "ruff",
            "check",
        ]
        + (["--fix"] if fix else []),
    ]
