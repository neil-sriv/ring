import functools
from typing import Any, Callable

import click

from dev_util.dev import cmd_run, dev_group


def compose_starter(profile: str) -> list[str]:
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


@dev_group("compose")
@click.pass_context
def compose(ctx: click.Context) -> None:
    pass


def compose_run(
    name: str,
    group: click.Group = compose,
    *args: Any,
    profile: str = "dev",
) -> Callable[[Callable[..., list[str]]], click.Command]:
    def decorator(f: Callable[..., list[str]]) -> click.Command:
        @cmd_run(name, group, *args)
        @click.option("--profile", type=str, default=profile)
        @functools.wraps(f)
        def inner(
            ctx: click.Context,
            *args: list[Any],
            **kwargs: dict[Any, Any],
        ) -> list[str]:
            profile = kwargs.pop("profile")
            cmd_string = f(ctx, *args, **kwargs)
            return compose_starter(profile) + cmd_string + ctx.args  # type: ignore

        return inner

    return decorator


def compose_exec(
    name: str,
    group: click.Group = compose,
    service: str | None = None,
    directory: str | None = None,
    cmd: str = "exec",
    **kwargs: Any,
) -> Callable[[Callable[..., list[str]]], click.Command]:
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
            cmd_string = f(ctx, *args, **kwargs)
            working_dir = f"/src/{directory}" if directory else "/src"
            return [cmd, "-w", working_dir] + [service] + cmd_string

        return inner

    return decorator


@compose_run("ps")
def compose_ps(
    ctx: click.Context,
    script: str,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return [
        "ps",
    ]


@compose_run("any")
def compose_any(
    ctx: click.Context,
    script: str,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return []


@compose_run("up")
def compose_up(
    ctx: click.Context,
    script: str,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return [
        "up",
        "--build",
        "--detach",
    ]
