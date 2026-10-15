from __future__ import annotations

from typing import Any

import click

from dev_util.dev import dev_command, dev_group


@dev_group("gen")
@click.pass_context
def gen(ctx: click.Context) -> None:
    pass


@dev_command("imports", gen)
@click.option(
    "--check",
    is_flag=True,
    default=False,
    help="Fail if generated import factories are stale.",
)
def gen_imports(
    ctx: click.Context,
    check: bool,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> None:
    """Regenerate decorator-registry import factories, or check freshness."""
    from ring.lib.gen_imports import (
        ImportFactoryError,
        check_generated_imports,
        write_generated_imports,
    )

    try:
        if check:
            diff = check_generated_imports()
            if diff:
                raise click.ClickException(
                    "Generated import files are stale. "
                    "Run `ring gen imports`.\n"
                    f"{diff}"
                )
            click.echo("Generated import files are up to date.")
            return
        for path in write_generated_imports():
            click.echo(f"Wrote {path}")
    except ImportFactoryError as exc:
        raise click.ClickException(str(exc)) from exc
