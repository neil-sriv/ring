#!/usr/bin/env python

import os
from pathlib import Path
import click
import subprocess
import functools
from typing import Any, TypeVar, ParamSpec, Callable

ROOT_DIR = Path(
    os.environ.get("ROOT_DIR", Path(__file__)).resolve().parents[1],  # type: ignore
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


def dev_command(
    name: str, group: click.Group
) -> Callable[[Callable[P, None]], click.Command]:
    def decorator(f: Callable[P, None]) -> click.Command:
        @group.command(name=name, context_settings=UNLIMITED_ARGS_SETTINGS)
        @functools.wraps(f)
        def inner(*args: P.args, **kwargs: P.kwargs) -> None:
            return f(*args, **kwargs)

        return inner

    return decorator


def cmd_run(
    name: str,
    group: click.Group,
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
                cmd_string + additional_args,
                cwd=ROOT_DIR,
            )

        return inner

    return decorator


from .compose import compose, compose_any, compose_ps, compose_up  # noqa: E402, F401
from .database import db, db_pgcli  # noqa: E402, F401
from .docker import docker, tag, push, push_and_tag  # noqa: E402, F401

if __name__ == "__main__":
    dev()
