from __future__ import annotations

from pathlib import Path
from typing import Any

import click

from dev_util.dev import ROOT_DIR, dev_command, dev_group


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


@dev_command("genesis-idp", gen)
@click.option(
    "--check",
    is_flag=True,
    default=False,
    help="Fail if vendored genesis-idp files were hand-edited.",
)
@click.option(
    "--from",
    "genesis_root",
    type=click.Path(path_type=Path, exists=True, file_okay=False),
    default=None,
    help="Local neil/genesis checkout to recopy sdk/python/idp from.",
)
@click.option(
    "--commit",
    default=None,
    help="Commit recorded in VENDORED_FROM (default: HEAD of --from).",
)
def gen_genesis_idp(
    ctx: click.Context,
    check: bool,
    genesis_root: Path | None,
    commit: str | None,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> None:
    """Vendor genesis-idp from a local genesis clone, or verify checksums."""
    from ring.lib.vendor_genesis_idp import (
        VendorGenesisIdpError,
        check_vendored_tree,
        vendor_from_genesis,
    )

    try:
        if check:
            diff = check_vendored_tree()
            if diff:
                raise click.ClickException(
                    "Vendored genesis-idp does not match the checksum "
                    "manifest. Recopy with `ring gen genesis-idp --from "
                    "<neil/genesis clone>`, or restore the files.\n"
                    f"{diff}"
                )
            click.echo("Vendored genesis-idp checksums match.")
            return
        if genesis_root is None:
            raise click.ClickException(
                "Pass --from /path/to/neil/genesis to recopy, or --check "
                "to verify the committed snapshot (offline)."
            )
        path = vendor_from_genesis(
            genesis_root.resolve(),
            commit=commit,
        )
        click.echo(f"Vendored genesis-idp into {path.relative_to(ROOT_DIR)}")
    except VendorGenesisIdpError as exc:
        raise click.ClickException(str(exc)) from exc
