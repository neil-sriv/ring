from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click

from dev_util.dev import cmd_run, dev_group

FE_DIR = Path(Path(__file__).resolve().parents[1], "react")


@dev_group("fe")
@click.pass_context
def fe(ctx: click.Context) -> None:
    pass


@cmd_run("install", fe, cwd=FE_DIR)
def fe_install(
    ctx: click.Context,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return ["pnpm", "install"]


@cmd_run("dev", fe, cwd=FE_DIR)
def fe_dev(
    ctx: click.Context,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return ["pnpm", "run", "dev"]


@cmd_run("build", fe, cwd=FE_DIR)
def fe_build(
    ctx: click.Context,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return ["pnpm", "run", "build"]


@cmd_run("regen", fe, cwd=FE_DIR)
def fe_regen(
    ctx: click.Context,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[list[str]]:
    spec_result = ctx.invoke(fe_spec)
    if not spec_result or not spec_result[0]:
        raise click.ClickException(
            "Failed to fetch OpenAPI spec from http://localhost:8001 "
            "(is the API container running? try `ring compose up`)."
        )
    try:
        spec_json = json.loads(spec_result[0])
    except json.JSONDecodeError as e:
        raise click.ClickException(
            f"OpenAPI response was not valid JSON: {e}"
        ) from e
    openapi_path = FE_DIR / "openapi.json"
    with open(openapi_path, "w") as f:
        json.dump(spec_json, f, indent=2)
        f.write("\n")
    click.echo(f"Wrote OpenAPI spec to {openapi_path}")
    return [
        ["node", "modify-openapi-operationids.js"],
        ["pnpm", "run", "generate-client"],
    ]


@cmd_run("spec", fe, cwd=FE_DIR, capture_output=True)
def fe_spec(
    ctx: click.Context,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return ["curl", "http://localhost:8001/api/v1/openapi.json"]
