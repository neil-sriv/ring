from __future__ import annotations

from typing import Any

import click

from dev_util.compose import compose_exec
from dev_util.dev import dev_group


@dev_group("letters")
@click.pass_context
def letters(ctx: click.Context) -> None:
    """Ops commands for cyclic letters."""


@compose_exec("create-next", letters, "api")
def create_next(
    ctx: click.Context,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> list[str]:
    """Create the next upcoming cyclic letter for a group.

    Usage:
        ring letters create-next grp_<uuid>
        ring letters create-next --dry-run grp_<uuid>
    """
    return [
        "python",
        "ring/scripts/create_next_letter.py",
    ]
