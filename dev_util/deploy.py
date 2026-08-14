from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import click

from dev_util.compose import compose_starter
from dev_util.deploy_status import (
    DEFAULT_BASE_URL,
    as_dict,
    collect,
    commits_behind,
    format_component,
)
from dev_util.dev import ROOT_DIR, dev_command, dev_group, subprocess_run
from dev_util.docker import (
    COMPOSE_SERVICE_BY_IMAGE,
    IMAGE_TAG_NAMES,
    push,
    tag,
)
from dev_util.frontend import fe_build

DEFAULT_VITE_API_URL = "https://ring.neilsriv.tech"
DEFAULT_AWS_REGION = "us-east-1"
ECR_PUBLIC_REGISTRY = "public.ecr.aws"
MANUAL_DEPLOY_IMAGES = ("ring-llm",)
DEPLOY_HOST_SCRIPT = Path(ROOT_DIR) / "dev_util" / "deploy_host.sh"


@dev_group("deploy")
@click.pass_context
def deploy(ctx: click.Context) -> None:
    pass


def _ecr_public_login(region: str) -> None:
    password = subprocess_run(
        ["aws", "ecr-public", "get-login-password", "--region", region],
        capture_output=True,
    ).stdout.strip()
    subprocess_run(
        [
            "docker",
            "login",
            "--username",
            "AWS",
            "--password-stdin",
            ECR_PUBLIC_REGISTRY,
        ],
        input=password,
    )


def _build_llm_image() -> None:
    subprocess_run(
        [
            "docker",
            "compose",
            "-f",
            "llm/compose.llm.yml",
            "-f",
            "llm/compose.prod.llm.yml",
            "--profile",
            "prod",
            "build",
            "llm",
        ]
    )


@dev_command("prod", deploy)
@click.option(
    "--vite-api-url",
    type=str,
    default=DEFAULT_VITE_API_URL,
    show_default=True,
    help="VITE_API_URL build arg baked into the frontend image.",
)
@click.option(
    "--maintenance-mode/--no-maintenance-mode",
    default=False,
    show_default=True,
    help="VITE_MAINTENANCE_MODE build arg baked into the frontend image.",
)
@click.option(
    "--region",
    type=str,
    default=DEFAULT_AWS_REGION,
    show_default=True,
    help="AWS region used for the public ECR login.",
)
@click.option(
    "--skip-fe-build",
    is_flag=True,
    default=False,
    help="Skip the `ring fe build` step (use the existing react/dist).",
)
@click.option(
    "--skip-login",
    is_flag=True,
    default=False,
    help="Skip the public ECR `docker login` step.",
)
@click.option(
    "--image",
    "-i",
    type=click.Choice(IMAGE_TAG_NAMES),
    multiple=True,
    default=MANUAL_DEPLOY_IMAGES,
    help="Images to build and push (default: ring-llm only).",
)
@click.option(
    "--extra-tag",
    "-t",
    multiple=True,
    default=(),
    help="Additional image tag(s) besides :latest (e.g. git SHA).",
)
def deploy_prod(
    ctx: click.Context,
    vite_api_url: str,
    maintenance_mode: bool,
    region: str,
    skip_fe_build: bool,
    skip_login: bool,
    image: tuple[str, ...],
    extra_tag: tuple[str, ...],
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> None:
    """Build, tag, and push production images to public ECR.

    ring-api publishes via CI on push to dev and deploys via Deploy ring-api.
    Frontend prod is Cloudflare. Only ring-llm still uses laptop builds.
    """
    images = list(image) or list(MANUAL_DEPLOY_IMAGES)
    # Kept usable on purpose: if CI or ECR is down, a laptop build is the
    # only way to ship. Confirm rather than block.
    for retired, reason in (
        ("ring-api", "CI publishes it on every push to dev"),
        ("ring-frontend", "prod frontend is Cloudflare Workers"),
    ):
        if retired in images:
            click.confirm(
                f"{retired} is no longer built from a laptop ({reason}). "
                "Continue anyway?",
                abort=True,
            )
    compose_services = [
        COMPOSE_SERVICE_BY_IMAGE[name]
        for name in images
        if name in COMPOSE_SERVICE_BY_IMAGE
    ]

    if not skip_fe_build and "ring-frontend" in images:
        ctx.invoke(fe_build)

    build_env = {
        **os.environ,
        "VITE_API_URL": vite_api_url,
        "VITE_MAINTENANCE_MODE": "true" if maintenance_mode else "false",
    }
    if compose_services:
        subprocess_run(
            compose_starter("prod") + ["build", *compose_services],
            env=build_env,
        )
    if "ring-llm" in images:
        _build_llm_image()

    if not skip_login:
        _ecr_public_login(region)

    ctx.invoke(tag, image=images, extra_tag=extra_tag)
    ctx.invoke(push, image=images, extra_tag=extra_tag)


@dev_command("status", deploy)
@click.option(
    "--base-url",
    type=str,
    default=DEFAULT_BASE_URL,
    show_default=True,
    help="Origin to probe.",
)
@click.option(
    "--ref",
    type=str,
    default="origin/dev",
    show_default=True,
    help="Git ref to measure deployed commits against.",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Emit machine-readable JSON instead of a table.",
)
def deploy_status(
    ctx: click.Context,
    base_url: str,
    ref: str,
    as_json: bool,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> None:
    """Show which commit is live on prod, and how long ago it shipped.

    The frontend deploys itself on every push to dev (Cloudflare Workers
    Builds). The API auto-deploys after Publish ring-api on dev (Deploy
    ring-api); manual fallback is `ring deploy host` / deploy_host.sh.
    """
    components = collect(base_url)
    behind_by_name = {
        component.name: (
            commits_behind(component.sha, ref) if component.sha else None
        )
        for component in components
    }

    if as_json:
        click.echo(
            json.dumps(
                {
                    "base_url": base_url,
                    "ref": ref,
                    "components": [
                        as_dict(component, behind_by_name[component.name])
                        for component in components
                    ],
                },
                indent=2,
            )
        )
        return

    click.echo(f"Deployed at {base_url}")
    for component in components:
        click.echo(
            f"  {format_component(component, behind_by_name[component.name], ref)}"
        )


@dev_command("history", deploy)
@click.option(
    "--limit",
    "-n",
    type=int,
    default=20,
    show_default=True,
    help="Max rows to show.",
)
@click.option(
    "--resolve/--no-resolve",
    default=False,
    show_default=True,
    help="Parse Actions logs for Deploy complete (<sha>) when no "
    "GitHub Deployment records exist yet (slower).",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Emit machine-readable JSON instead of a table.",
)
def deploy_history(
    ctx: click.Context,
    limit: int,
    resolve: bool,
    as_json: bool,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> None:
    """List recent API deploys so you can pick a rollback SHA.

    Prefers GitHub Deployments recorded by Deploy ring-api
    (environment=production-api). Falls back to workflow runs; pass
    --resolve to parse logs for the exact image SHA.
    """
    from dev_util.deploy_history import as_dicts, collect, format_record

    try:
        records = collect(limit, resolve_logs=resolve)
    except FileNotFoundError as exc:
        raise click.ClickException(
            "gh CLI not found — install GitHub CLI to use deploy history."
        ) from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or str(exc)).strip()
        raise click.ClickException(detail or "gh command failed") from exc

    if as_json:
        click.echo(json.dumps({"deployments": as_dicts(records)}, indent=2))
        return

    if not records:
        click.echo(
            "No deploy history yet. Successful Deploy ring-api runs record "
            "a GitHub Deployment (production-api); older runs need --resolve "
            "to parse logs."
        )
        return

    click.echo("API deploy history (newest first) — use sha with:")
    click.echo(
        "  Actions → Deploy ring-api, or ./dev_util/deploy_host.sh <sha>"
    )
    click.echo("")
    for record in records:
        click.echo(format_record(record))


@dev_command("host", deploy)
@click.option(
    "--skip-git/--no-skip-git",
    default=False,
    show_default=True,
    help="Skip git fetch/checkout.",
)
@click.option(
    "--skip-pull/--no-skip-pull",
    default=False,
    show_default=True,
    help="Skip `prod.sh` image pull.",
)
@click.option(
    "--skip-migrate/--no-skip-migrate",
    default=False,
    show_default=True,
    help="Skip `ring db upgrade --profile prod`.",
)
@click.option(
    "--skip-verify/--no-skip-verify",
    default=False,
    show_default=True,
    help="Skip GET /api/v1/version gate.",
)
@click.option(
    "--rollback-on-fail/--no-rollback-on-fail",
    default=False,
    show_default=True,
    help="Re-run against the pre-deploy image SHA if version verify fails.",
)
@click.argument("sha", required=False, default=None)
def deploy_host(
    ctx: click.Context,
    skip_git: bool,
    skip_pull: bool,
    skip_migrate: bool,
    skip_verify: bool,
    rollback_on_fail: bool,
    sha: str | None,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> None:
    """Roll out a SHA-tagged API image on the current host (EC2)."""
    cmd = ["bash", str(DEPLOY_HOST_SCRIPT)]
    if skip_git:
        cmd.append("--skip-git")
    if skip_pull:
        cmd.append("--skip-pull")
    if skip_migrate:
        cmd.append("--skip-migrate")
    if skip_verify:
        cmd.append("--skip-verify")
    if rollback_on_fail:
        cmd.append("--rollback-on-fail")
    if sha:
        cmd.append(sha)
    subprocess_run(cmd)
