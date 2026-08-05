"""Cursor Cloud Agent helpers exposed via the `ring` CLI.

Primary use: point a local Vite + API stack at CockroachDB Cloud so frontend
work can exercise real production data without hitting ring.neilsriv.tech
from the browser.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

import click

from dev_util.dev import (
    ROOT_DIR,
    UNLIMITED_ARGS_SETTINGS,
    dev_group,
    subprocess_run,
)

STATE_DIR = ROOT_DIR / ".ring-cloud-prod-db"
MARKER_PATH = STATE_DIR / "mode"
ENV_BACKUP_PATH = STATE_DIR / ".env.local-backup"
ENV_PATH = ROOT_DIR / ".env"
CA_PATH = Path.home() / ".postgresql" / "root.crt"

LOCAL_COCKROACH_URI = "cockroachdb://ringcockroach:ringcockroach@cockroach:26257/ring?sslmode=require"

# Ring has one live Cockroach Cloud cluster. Despite its name, `ring-db-staging`
# is what ring.neilsriv.tech serves from; `ring-db` is stale and unused. There is
# no safe "staging" copy to fall back to — every connection here is live data.
COCKROACH_URI_SECRET = "RING_COCKROACH_DATABASE_URI"
CA_CERT_SECRET = "RING_COCKROACH_CA_CERT"


def _compose_cmd(*, cloud_override: bool) -> list[str]:
    files = ["compose.core.yml", "compose.dev.yml"]
    if cloud_override:
        files.append("compose.cloud-prod-db.yml")
    cmd = ["docker", "compose"]
    for path in files:
        cmd.extend(["-f", path])
    cmd.extend(["--profile", "dev"])
    return cmd


def _require_env_file() -> None:
    if not ENV_PATH.is_file():
        raise click.ClickException(
            "Missing .env — run bash .cursor/cloud-start.sh --bootstrap-only first"
        )


def _current_mode() -> str:
    if MARKER_PATH.is_file():
        return MARKER_PATH.read_text(encoding="utf-8").strip() or "local"
    return "local"


def _read_env_var(key: str, path: Path = ENV_PATH) -> str:
    if not path.is_file():
        return ""
    value = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{key}="):
            value = line.split("=", 1)[1]
    return value


def _upsert_env_var(key: str, value: str) -> None:
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    prefix = f"{key}="
    replaced = False
    new_lines: list[str] = []
    for line in lines:
        if line.startswith(prefix):
            new_lines.append(f"{key}={value}")
            replaced = True
        else:
            new_lines.append(line)
    if not replaced:
        new_lines.append(f"{key}={value}")
    ENV_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def _uri_host_hint(uri: str) -> str:
    if not uri:
        return ""
    parsed = urlparse(uri)
    if parsed.hostname:
        return parsed.hostname
    match = re.match(r"^[a-z0-9+.-]+://(?:[^/@]+@)?([^:/?]+)", uri)
    return match.group(1) if match else ""


def _resolve_uri() -> str:
    uri = os.environ.get(COCKROACH_URI_SECRET, "").strip()
    if not uri:
        raise click.ClickException(f"Missing secret {COCKROACH_URI_SECRET}")
    return uri


def _ensure_ca_cert() -> None:
    CA_PATH.parent.mkdir(parents=True, exist_ok=True)
    pem = os.environ.get(CA_CERT_SECRET, "").strip()
    if pem:
        CA_PATH.write_text(pem + "\n", encoding="utf-8")
        CA_PATH.chmod(0o600)
        click.echo(f"Wrote Cockroach CA cert to {CA_PATH}")
        return
    if CA_PATH.is_file():
        click.echo(f"Using existing Cockroach CA cert at {CA_PATH}")
        return
    raise click.ClickException(
        f"Missing Cockroach CA cert at {CA_PATH}. "
        f"Set Cursor secret {CA_CERT_SECRET} (PEM) or place root.crt at that path."
    )


def _confirm_or_die(host: str, assume_yes: bool) -> None:
    click.echo(
        "\n"
        "!!! WARNING: connecting to LIVE production data !!!\n"
        f"  SQL host:   {host}\n"
        "  Frontend:   http://localhost:5173  (Vite → local API → prod DB)\n"
        "  Scheduler:  DISABLED\n"
        "  There is no staging copy — writes affect real users.\n"
        "  Do NOT run migrations against this database from the cloud agent.\n"
    )
    if assume_yes:
        return
    if not click.get_text_stream("stdin").isatty():
        raise click.ClickException(
            "Non-interactive shell: pass --yes to confirm."
        )
    answer = click.prompt(
        "Type 'prod' to continue", default="", show_default=False
    )
    if answer != "prod":
        raise click.ClickException("Aborted.")


def _restart_api(*, cloud_override: bool) -> None:
    subprocess_run(
        _compose_cmd(cloud_override=cloud_override)
        + ["up", "--detach", "--force-recreate", "api"],
        cwd=ROOT_DIR,
    )


def _wait_for_api(timeout_s: int = 90) -> None:
    deadline = time.time() + timeout_s
    url = "http://localhost:8001/api/v1/openapi.json"
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if 200 <= response.status < 300:
                    return
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(2)
    raise click.ClickException(
        "API did not become ready after switching DB mode"
    )


def _http_ok(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, TimeoutError):
        return False


def _probe_db_via_api() -> bool:
    result = subprocess.run(
        [
            "docker",
            "exec",
            "ring-api",
            "python",
            "-c",
            "from sqlalchemy import text\n"
            "from ring.sqlalchemy_base import engine\n"
            "with engine.connect() as conn:\n"
            "    conn.execute(text('SELECT 1'))\n"
            "print('ok')\n",
        ],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def _probe_local_cockroach() -> bool:
    result = subprocess.run(
        [
            "docker",
            "exec",
            "ring-cockroach",
            "./cockroach",
            "sql",
            "--certs-dir=/root/.cockroach-certs",
            "-d",
            "ring",
            "-e",
            "SELECT 1",
        ],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


@dev_group("cloud")
@click.pass_context
def cloud(ctx: click.Context) -> None:
    """Cursor Cloud Agent helpers."""


@cloud.group(
    "prod-db",
    context_settings=UNLIMITED_ARGS_SETTINGS,
    help=(
        "Point the local Cloud Agent Vite + API stack at the live CockroachDB "
        "Cloud database."
    ),
)
@click.pass_context
def prod_db(ctx: click.Context) -> None:
    pass


@prod_db.command("status")
def prod_db_status() -> None:
    """Show current mode and secret/cert readiness."""
    _require_env_file()
    mode = _current_mode()
    uri = _read_env_var("COCKROACH_DATABASE_URI")
    host = _uri_host_hint(uri)
    ca_state = "present" if CA_PATH.is_file() else "missing"
    click.echo(f"mode:              {mode}")
    click.echo(f"COCKROACH host:    {host or '<unset>'}")
    click.echo(f"ENVIRONMENT:       {_read_env_var('ENVIRONMENT')}")
    click.echo(f"DISABLE_SCHEDULER: {_read_env_var('DISABLE_SCHEDULER')}")
    click.echo(f"CA cert:           {ca_state} ({CA_PATH})")
    click.echo(
        "URI secret:        "
        + ("set" if os.environ.get(COCKROACH_URI_SECRET) else "unset")
    )
    click.echo(
        "CA secret:         "
        + ("set" if os.environ.get(CA_CERT_SECRET) else "unset")
    )


@prod_db.command("enable")
@click.option(
    "--yes",
    "-y",
    "assume_yes",
    is_flag=True,
    default=False,
    help="Skip the interactive confirmation prompt.",
)
def prod_db_enable(assume_yes: bool) -> None:
    """Point local API at Cockroach Cloud and recreate the API container."""
    _require_env_file()
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    uri = _resolve_uri()
    host = _uri_host_hint(uri)
    _confirm_or_die(host, assume_yes)
    _ensure_ca_cert()

    if not ENV_BACKUP_PATH.is_file():
        shutil.copy2(ENV_PATH, ENV_BACKUP_PATH)
        click.echo(f"Backed up .env to {ENV_BACKUP_PATH}")

    _upsert_env_var("COCKROACH_DATABASE_URI", uri)
    _upsert_env_var("ENVIRONMENT", "cloud-prod-db")
    _upsert_env_var("DISABLE_SCHEDULER", "true")
    # Keep Vite same-origin proxy; do not point the browser at prod nginx.
    _upsert_env_var("VITE_API_URL", "")

    MARKER_PATH.write_text("prod\n", encoding="utf-8")

    click.echo("Recreating API with compose.cloud-prod-db.yml…")
    _restart_api(cloud_override=True)
    _wait_for_api()

    click.echo(
        "\n=== cloud-prod-db enabled (prod) ===\n"
        "  App:     http://localhost:5173\n"
        "  API:     http://localhost:8001/api/v1/docs\n"
        f"  DB host: {host}\n"
        "  Login:   use a real prod user "
        "(seeded test@example.com is local-only)\n"
        "  Disable: ring cloud prod-db disable\n"
        "  Health:  ring cloud prod-db health\n"
    )


@prod_db.command("disable")
def prod_db_disable() -> None:
    """Restore local Cockroach URI and recreate the API container."""
    _require_env_file()
    if _current_mode() == "local" and not ENV_BACKUP_PATH.is_file():
        click.echo("Already in local mode.")
        return

    if ENV_BACKUP_PATH.is_file():
        local_uri = _read_env_var("COCKROACH_DATABASE_URI", ENV_BACKUP_PATH)
        if not local_uri:
            local_uri = LOCAL_COCKROACH_URI
    else:
        local_uri = LOCAL_COCKROACH_URI

    _upsert_env_var("COCKROACH_DATABASE_URI", local_uri)
    _upsert_env_var("ENVIRONMENT", "local")
    _upsert_env_var("DISABLE_SCHEDULER", "false")
    if MARKER_PATH.is_file():
        MARKER_PATH.unlink()

    click.echo("Recreating API against local Cockroach…")
    _restart_api(cloud_override=False)
    _wait_for_api()
    click.echo("=== cloud-prod-db disabled (local Cockroach) ===")


@prod_db.command("health")
def prod_db_health() -> None:
    """Verify API is up and can query the active database."""
    _require_env_file()
    mode = _current_mode()
    errors = 0

    def check(label: str, ok: bool) -> None:
        nonlocal errors
        if ok:
            click.echo(f"OK  {label}")
        else:
            click.echo(f"FAIL {label}", err=True)
            errors += 1

    check("API openapi", _http_ok("http://localhost:8001/api/v1/openapi.json"))
    check("API docs", _http_ok("http://localhost:8001/api/v1/docs"))

    if mode != "local":
        check("CA cert present", CA_PATH.is_file())
        sched = _read_env_var("DISABLE_SCHEDULER")
        check(
            f"DISABLE_SCHEDULER={sched}",
            sched in {"true", "1"},
        )
        check("cloud DB SELECT 1 via API container", _probe_db_via_api())
    else:
        check("local Cockroach", _probe_local_cockroach())

    click.echo(f"mode: {mode}")
    if errors:
        raise click.ClickException(f"{errors} check(s) failed")
    click.echo("cloud-prod-db health OK")
