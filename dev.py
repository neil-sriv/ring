#!/usr/bin/env python

import os
from pathlib import Path
import click
import subprocess
import functools
from typing import Any, TypeVar, ParamSpec, Callable

ROOT_DIR = Path(
    os.environ.get("ROOT_DIR", Path(__file__)).resolve().parents[0],  # type: ignore
)
UNLIMITED_ARGS_SETTINGS = {
    "ignore_unknown_options": True,
    "allow_extra_args": True,
}
T = TypeVar("T")
P = ParamSpec("P")


def subprocess_run(
    cmd: list[str],
    **kwargs: Any,
) -> subprocess.CompletedProcess[str]:
    print(" ".join(cmd))
    return subprocess.run(cmd, check=True, text=True, **kwargs)


@click.group(
    context_settings=UNLIMITED_ARGS_SETTINGS,
)
@click.pass_context
def dev(ctx: click.Context):
    pass


def dev_group(
    name: str, invoke_without_command: bool = False
) -> Callable[[Callable[P, None]], click.Group]:
    def decorator(f: Callable[P, None]) -> click.Group:
        @dev.group(
            name=name,
            context_settings=UNLIMITED_ARGS_SETTINGS,
            invoke_without_command=invoke_without_command,
        )
        @functools.wraps(f)
        def inner(*args: P.args, **kwargs: P.kwargs) -> None:
            return f(*args, **kwargs)

        return inner

    return decorator


def dev_command(name: str) -> Callable[[Callable[P, None]], click.Command]:
    def decorator(f: Callable[P, None]) -> click.Command:
        @dev.command(name=name, context_settings=UNLIMITED_ARGS_SETTINGS)
        @functools.wraps(f)
        def inner(*args: P.args, **kwargs: P.kwargs) -> None:
            return f(*args, **kwargs)

        return inner

    return decorator


def cmd_run(
    name: str, group: click.Group
) -> Callable[[Callable[P, list[str]]], click.Command]:
    def decorator(f: Callable[P, list[str]]) -> click.Command:
        @group.command(name=name, context_settings=UNLIMITED_ARGS_SETTINGS)
        @click.pass_context
        @functools.wraps(f)
        def inner(
            ctx: click.Context, *args: P.args, **kwargs: P.kwargs
        ) -> subprocess.CompletedProcess[str]:
            cmd_string = f(*args, **kwargs)
            additional_args = ctx.args
            return subprocess_run(
                COMPOSE_CMD_STARTER + cmd_string + additional_args,
                cwd=ROOT_DIR,
            )

        return inner

    return decorator


COMPOSE_CMD_STARTER = [
    "docker",
    "compose",
    "-f",
    "compose.core.yml",
    "-f",
    "compose.dev.yml",
    "--profile",
    "dev",
]


@dev_group("compose")
@click.pass_context
def compose(ctx: click.Context) -> None:
    pass


@cmd_run("ps", compose)
def compose_ps() -> list[str]:
    return [
        "ps",
    ]


@cmd_run("any", compose)
def compose_any() -> list[str]:
    return []


@cmd_run("up", compose)
def compose_up() -> list[str]:
    return [
        "up",
        "--build",
        "--detach",
    ]


if __name__ == "__main__":
    dev()
