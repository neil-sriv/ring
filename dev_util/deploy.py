from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import click

from dev_util.compose import compose_starter
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
DEFAULT_DEPLOY_IMAGES = ("ring-api",)
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
    default=DEFAULT_DEPLOY_IMAGES,
    help="Images to build and push (default: ring-api).",
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

    Default is ring-api only. Frontend prod is Cloudflare; ring-llm is
    manual. Laptop builds are the fallback — CI publishes SHA tags on
    push to dev.
    """
    images = list(image) or list(DEFAULT_DEPLOY_IMAGES)
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
    help="Re-run against the pre-deploy SHA if version verify fails.",
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
