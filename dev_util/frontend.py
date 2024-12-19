from pathlib import Path
from typing import Any

import click

from dev_util.dev import cmd_run, dev_group

FE_DIR = Path(Path(__file__).resolve().parents[1], "react")


@dev_group("fe")
@click.pass_context
def fe(ctx: click.Context) -> None:
    pass


@cmd_run("dev", fe, cwd=FE_DIR)
def fe_dev(
    ctx: click.Context,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    print(ctx.args)
    return ["yarn", "run", "dev"]


@cmd_run("build", fe, cwd=FE_DIR)
def fe_build(
    ctx: click.Context,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return ["yarn", "run", "build"]


@cmd_run("regen", fe, cwd=FE_DIR)
def fe_regen(
    ctx: click.Context,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return (
        ["node", "modify-openapi-operationids.js"]
        + ["&&"]
        + ["yarn", "run", "generate-client"]
    )
