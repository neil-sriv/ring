import functools
from typing import Any, Callable
import click
from dev_util.dev import cmd_run, dev_group


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


def compose_run(
    name: str,
    group: click.Group | None = None,
) -> Callable[[Callable[..., list[str]]], click.Command]:
    def decorator(f: Callable[..., list[str]]) -> click.Command:
        @cmd_run(name, group if group else compose)
        @functools.wraps(f)
        def inner(*args: Any, **kwargs: Any) -> list[str]:
            cmd_string = f(*args, **kwargs)
            return COMPOSE_CMD_STARTER + cmd_string

        return inner

    return decorator


@dev_group("compose")
@click.pass_context
def compose(ctx: click.Context) -> None:
    pass


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
