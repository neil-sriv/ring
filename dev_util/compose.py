import functools
from typing import Any, Callable
import click
from dev_util.dev import cmd_run, dev_group


def compose_starter(prod: bool = False) -> list[str]:
    return [
        "docker",
        "compose",
        "-f",
        "compose.core.yml",
        "-f",
        "compose.prod.yml" if prod else "compose.dev.yml",
    ] + ([] if prod else ["--profile", "dev"])


@dev_group("compose")
@click.pass_context
def compose(ctx: click.Context) -> None:
    pass


def compose_run(
    name: str,
    group: click.Group = compose,
) -> Callable[[Callable[..., list[str]]], click.Command]:
    def decorator(f: Callable[..., list[str]]) -> click.Command:
        @cmd_run(name, group)
        @click.option(
            "--prod",
            is_flag=True,
            default=False,
        )
        @functools.wraps(f)
        def inner(prod: bool, *args: Any, **kwargs: Any) -> list[str]:
            cmd_string = f(*args, **kwargs)
            return compose_starter(prod) + cmd_string

        return inner

    return decorator


def compose_exec(
    name: str,
    group: click.Group = compose,
    service: str | None = None,
    directory: str | None = None,
) -> Callable[[Callable[..., list[str]]], click.Command]:
    def decorator(f: Callable[..., list[str]]) -> click.Command:
        @compose_run(name, group)
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
            service: str,
            directory: str,
            *args: Any,
            **kwargs: Any,
        ) -> list[str]:
            cmd_string = f(*args, **kwargs)
            working_dir = f"/src/{directory}" if directory else "/src"
            return ["exec", "-w", working_dir] + [service] + cmd_string

        return inner

    return decorator


@compose_run("ps")
def compose_ps() -> list[str]:
    return [
        "ps",
    ]


@compose_run("any")
def compose_any() -> list[str]:
    return []


@compose_run("up")
def compose_up() -> list[str]:
    return [
        "up",
        "--build",
        "--detach",
    ]
