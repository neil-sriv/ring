#!/usr/bin/env python
from __future__ import annotations
import os
from pathlib import Path
import click
import subprocess
import functools
from typing import Any, Callable

ROOT_DIR = Path(
    Path(os.environ.get("ROOT_DIR")).resolve()
    if os.environ.get("ROOT_DIR")
    else Path(__file__).resolve().parents[1],  # type: ignore
)
UNLIMITED_ARGS_SETTINGS = {
    "ignore_unknown_options": True,
    "allow_extra_args": True,
}


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
) -> Callable[[Callable[..., None]], click.Group]:
    def decorator(f: Callable[..., None]) -> click.Group:
        @dev.group(
            name=name,
            context_settings=UNLIMITED_ARGS_SETTINGS,
            invoke_without_command=invoke_without_command,
        )
        @functools.wraps(f)
        def inner(*args: Any, **kwargs: Any) -> None:
            return f(*args, **kwargs)

        return inner

    return decorator


def dev_command(
    name: str, group: click.Group
) -> Callable[[Callable[..., None]], click.Command]:
    def decorator(f: Callable[..., None]) -> click.Command:
        @group.command(name=name, context_settings=UNLIMITED_ARGS_SETTINGS)
        @functools.wraps(f)
        def inner(*args: Any, **kwargs: Any) -> None:
            return f(*args, **kwargs)

        return inner

    return decorator


def cmd_run(
    name: str,
    group: click.Group,
) -> Callable[[Callable[..., list[str]]], click.Command]:
    def decorator(f: Callable[..., list[str]]) -> click.Command:
        @group.command(name=name, context_settings=UNLIMITED_ARGS_SETTINGS)
        @click.pass_context
        @functools.wraps(f)
        def inner(ctx: click.Context, *args: Any, **kwargs: Any) -> None:
            cmd_string = f(*args, **kwargs)
            additional_args = ctx.args
            try:
                subprocess_run(
                    cmd_string + additional_args,
                    cwd=ROOT_DIR,
                )
            except subprocess.CalledProcessError:
                pass

        return inner

    return decorator


from .compose import *  # noqa
from .database import *  # noqa
from .docker import *  # noqa
from .run import *  # noqa

if __name__ == "__main__":
    dev()
