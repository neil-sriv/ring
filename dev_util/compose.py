import functools
from typing import Callable
import click
from dev_util.dev import P, cmd_run, dev_group


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
) -> Callable[[Callable[P, list[str]]], click.Command]:
    def decorator(f: Callable[P, list[str]]) -> click.Command:
        @cmd_run(name, compose)
        @functools.wraps(f)
        def inner(*args: P.args, **kwargs: P.kwargs) -> list[str]:
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
