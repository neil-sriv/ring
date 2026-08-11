from __future__ import annotations

import functools
import sys
from pathlib import Path
from typing import Any, Callable

import click

from dev_util.dev import cmd_run, dev_group
from dev_util.git_meta import apply_git_build_args_to_environ
from dev_util.runtime_version import ensure_snapshot_file

_RUNTIME_VERSION_SCRIPT = Path(__file__).resolve().parent / (
    "runtime_version.py"
)


def compose_starter(profile: str) -> list[str]:
    apply_git_build_args_to_environ()
    if profile != "test":
        ensure_snapshot_file()
    profile_string = ["--profile", f"{profile}"]
    compose_file_strings: list[str] = []
    if profile == "test":
        compose_file_strings.append("compose.test.yml")
    else:
        compose_file_strings.append("compose.core.yml")
        if profile in ["prod", "certbot"]:
            compose_file_strings.append("compose.prod.yml")
        else:
            compose_file_strings.append("compose.dev.yml")
    compose_file = (" -f ".join(compose_file_strings)).split(" ")
    return (
        [
            "docker",
            "compose",
            "-f",
        ]
        + compose_file
        + profile_string
    )


def _compose_with_snapshot(
    profile: str,
    compose_cmd: list[str],
) -> list[str] | list[list[str]]:
    if profile == "test":
        return compose_cmd
    return [
        compose_cmd,
        [sys.executable, str(_RUNTIME_VERSION_SCRIPT), "write"],
    ]


@dev_group("compose")
@click.pass_context
def compose(ctx: click.Context) -> None:
    pass


def compose_run(
    name: str,
    group: click.Group = compose,
    *args: Any,
    profile: str = "dev",
    **kwargs: Any,
) -> Callable[[Callable[..., list[str]]], click.Command]:
    def decorator(f: Callable[..., list[str]]) -> click.Command:
        @cmd_run(name, group, *args, **kwargs)
        @click.option("--profile", type=str, default=profile)
        @functools.wraps(f)
        def inner(
            ctx: click.Context,
            *args: list[Any],
            **kwargs: dict[Any, Any],
        ) -> list[str] | list[list[str]]:
            profile = kwargs.pop("profile")
            cmd_string = f(ctx, *args, **kwargs)
            compose_cmd = compose_starter(profile) + cmd_string + ctx.args  # type: ignore
            return _compose_with_snapshot(profile, compose_cmd)

        return inner

    return decorator


def compose_exec(
    name: str,
    group: click.Group = compose,
    service: str | None = None,
    directory: str | None = None,
    cmd: str = "exec",
    opts: list[str] | None = None,
    **kwargs: Any,
) -> Callable[[Callable[..., list[str]]], click.Command]:
    """
    Decorator for running commands in a service.

    Args:
        name: The name of the command.
        group: The group of the command.
        service: The service to run the command in.
        directory: The directory to run the command in.
        cmd: The command to run.
        opts: The options to pass to the command.
        **kwargs: Additional arguments to pass to the command.
    """

    def decorator(f: Callable[..., list[str]]) -> click.Command:
        @compose_run(name, group, **kwargs)
        @click.option(
            "--service",
            "-s",
            type=str,
            default=service,
        )
        @click.option(
            "--directory",
            "-d",
            type=str,
            default=directory,
        )
        @functools.wraps(f)
        def inner(
            ctx: click.Context,
            service: str,
            directory: str,
            *args: Any,
            **kwargs: Any,
        ) -> list[str]:
            nonlocal opts
            if opts is None:
                opts = []
            cmd_string = f(ctx, *args, **kwargs)

            # Handle working directory - if directory is explicitly None, don't set working dir
            if directory is None:
                working_dir_args = []
            else:
                working_dir = f"/src/{directory}" if directory else "/src"
                working_dir_args = ["-w", working_dir]

            return [cmd] + working_dir_args + opts + [service] + cmd_string

        return inner

    return decorator


@compose_run("ps")
def compose_ps(
    ctx: click.Context,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return [
        "ps",
    ]


@compose_run("any")
def compose_any(
    ctx: click.Context,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return []


@compose_run("up")
def compose_up(
    ctx: click.Context,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return [
        "up",
        "--build",
        "--detach",
    ]


def compose_cmd_run(
    name: str,
    group: click.Group = compose,
    profile: str = "dev",
    **kwargs: Any,
) -> Callable[[Callable[..., list[str]]], click.Command]:
    """
    Decorator that combines cmd_run with compose functionality.
    This allows direct control over compose commands while still using the cmd_run infrastructure.

    Args:
        name: The name of the command.
        group: The group of the command.
        profile: The compose profile to use.
        **kwargs: Additional arguments to pass to cmd_run.
    """

    def decorator(f: Callable[..., list[str]]) -> click.Command:
        # Filter out compose-specific parameters that cmd_run doesn't understand
        cmd_run_kwargs = {
            k: v
            for k, v in kwargs.items()
            if k not in ["service", "directory", "cmd", "opts"]
        }

        @cmd_run(name, group, **cmd_run_kwargs)
        @click.option("--profile", type=str, default=profile)
        @functools.wraps(f)
        def inner(
            ctx: click.Context,
            *args: list[Any],
            **kwargs: dict[Any, Any],
        ) -> list[str] | list[list[str]]:
            profile = kwargs.pop("profile")
            cmd_string = f(ctx, *args, **kwargs)
            compose_cmd = compose_starter(profile) + cmd_string + ctx.args  # type: ignore
            return _compose_with_snapshot(profile, compose_cmd)

        return inner

    return decorator
