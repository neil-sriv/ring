from __future__ import annotations

from pathlib import Path
from typing import Any

import click

from dev_util.dev import cmd_run, dev_group

FE_DIR = Path(Path(__file__).resolve().parents[1], "react")


@dev_group("fe")
def fe() -> None:
    pass


@cmd_run("install", fe, cwd=FE_DIR)
def fe_install(
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return ["pnpm", "install"]


@cmd_run("dev", fe, cwd=FE_DIR)
def fe_dev(
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return ["pnpm", "run", "dev"]


@cmd_run("build", fe, cwd=FE_DIR)
def fe_build(
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return ["pnpm", "run", "build"]


@cmd_run("regen", fe, cwd=FE_DIR)
def fe_regen(
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return (
        ["node", "modify-openapi-operationids.js"]
        + ["&&"]
        + ["pnpm", "run", "generate-client"]
    )
