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
    ] + ([] if prod else ["--profile", "ring"])


def compose_run(
    name: str,
    group: click.Group | None = None,
) -> Callable[[Callable[..., list[str]]], click.Command]:
    def decorator(f: Callable[..., list[str]]) -> click.Command:
        @cmd_run(name, group if group else compose)
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
