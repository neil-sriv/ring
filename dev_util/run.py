from typing import Any

import click

from dev_util.compose import compose_exec
from dev_util.dev import dev_group


@dev_group("run")
def run() -> None:
    pass


@compose_exec("script", run, "api")
@click.option("--script", type=str, required=True)
def run_script(
    script: str,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    script_cmd = [
        "python",
        "ring/scripts/script_runner.py",
        "run-script",
        f"{script}",
    ]
    return script_cmd


@compose_exec("shell", run, "api")
def run_shell(
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    return [
        "python",
        "ring/scripts/script_runner.py",
        "run-script",
        "ring/shell/shell.py",
    ]


# @run_script("sql", run)
# @click.argument("query", type=str)
# def sql(query: str) -> list[str]:
#     script_cmd = [
#         "python",
#         "ring/scripts/script_runner.py",
#         "run-script",
#         "ring/scripts/sql_script.py",
#         f"{query}",
#     ]
#     return ["docker", "exec", "ring-api"] + script_cmd
