"""Cursor Cloud Agent helpers exposed via the `ring` CLI."""

from __future__ import annotations

import os
import urllib.error
import urllib.request

import click

from dev_util.dev import (
    ROOT_DIR,
    UNLIMITED_ARGS_SETTINGS,
    dev_group,
    subprocess_run,
)

DEFAULT_PROD_API_URL = "https://ring.neilsriv.tech"
FE_DIR = ROOT_DIR / "react"


def _openapi_url(api_url: str) -> str:
    return f"{api_url.rstrip('/')}/api/v1/openapi.json"


def _check_prod_api(api_url: str) -> None:
    url = _openapi_url(api_url)
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            if not 200 <= response.status < 300:
                raise click.ClickException(
                    f"Prod API returned HTTP {response.status}: {url}"
                )
    except (urllib.error.URLError, TimeoutError) as exc:
        raise click.ClickException(
            f"Cannot reach prod API at {url}: {exc}"
        ) from exc
    click.echo(f"OK  prod API: {url}")


@dev_group("cloud")
@click.pass_context
def cloud(ctx: click.Context) -> None:
    """Cursor Cloud Agent helpers."""


@cloud.group(
    "client-only",
    context_settings=UNLIMITED_ARGS_SETTINGS,
    help="Run the local Vite frontend against Ring's production API.",
)
@click.pass_context
def client_only(ctx: click.Context) -> None:
    pass


@client_only.command("check")
@click.option(
    "--api-url",
    default=DEFAULT_PROD_API_URL,
    show_default=True,
    help="Production API origin.",
)
def client_only_check(api_url: str) -> None:
    """Verify the production API is reachable."""
    _check_prod_api(api_url)


@client_only.command("dev")
@click.option(
    "--api-url",
    default=DEFAULT_PROD_API_URL,
    show_default=True,
    help="API origin used by the Vite same-origin proxy.",
)
@click.option("--host", default="0.0.0.0", show_default=True)
@click.option("--port", default=5173, show_default=True, type=int)
@click.option(
    "--skip-check",
    is_flag=True,
    default=False,
    help="Start Vite even if the production API health check fails.",
)
def client_only_dev(
    api_url: str, host: str, port: int, skip_check: bool
) -> None:
    """Start Vite with /api/v1 proxied to the production API."""
    if skip_check:
        click.echo(
            f"Skipping prod API check; proxy target will be {api_url.rstrip('/')}"
        )
    else:
        _check_prod_api(api_url)
    click.echo(
        f"Starting client-only frontend: http://localhost:{port} "
        f"→ {api_url.rstrip('/')}"
    )
    env = {
        **os.environ,
        "VITE_API_URL": "",
        "VITE_API_PROXY_TARGET": api_url.rstrip("/"),
    }
    subprocess_run(
        ["pnpm", "run", "dev", "--host", host, "--port", str(port)],
        cwd=FE_DIR,
        env=env,
    )
