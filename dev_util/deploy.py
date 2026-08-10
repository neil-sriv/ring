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
    default=IMAGE_TAG_NAMES,
    help="Images to build and push (default: all).",
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
    """Build, tag, and push the production images to public ECR.

    Mirrors the manual prod deploy flow:
      1. ring fe build
      2. compose --profile prod build (with VITE_* build args)
      3. aws ecr-public login -> docker login
      4. ring docker tp (tag + push)
    """
    images = list(image) or list(IMAGE_TAG_NAMES)
    compose_services = [
        COMPOSE_SERVICE_BY_IMAGE[name]
        for name in images
        if name in COMPOSE_SERVICE_BY_IMAGE
    ]
    build_llm = "ring-llm" in images

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
    if build_llm:
        _build_llm_image()

    if not skip_login:
        _ecr_public_login(region)

    ctx.invoke(tag, image=images, extra_tag=extra_tag)
    ctx.invoke(push, image=images, extra_tag=extra_tag)


@dev_command("host", deploy)
@click.option(
    "--ref",
    type=str,
    default=None,
    help="Git ref/SHA to check out before rolling out (default: leave as-is).",
)
@click.option(
    "--skip-git/--no-skip-git",
    default=False,
    show_default=True,
    help="Skip git fetch/checkout.",
)
@click.option(
    "--skip-migrate/--no-skip-migrate",
    default=False,
    show_default=True,
    help="Skip `ring db upgrade`.",
)
@click.option(
    "--image",
    "-i",
    type=click.Choice(IMAGE_TAG_NAMES),
    multiple=True,
    default=("ring-api", "ring-frontend"),
    help="Images to pull from ECR (default: api + frontend).",
)
def deploy_host(
    ctx: click.Context,
    ref: str | None,
    skip_git: bool,
    skip_migrate: bool,
    image: tuple[str, ...],
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> None:
    """Pull ECR images and roll out Compose on the current host (EC2)."""
    cmd = ["bash", str(DEPLOY_HOST_SCRIPT)]
    if ref:
        cmd.extend(["--ref", ref])
    if skip_git:
        cmd.append("--skip-git")
    if skip_migrate:
        cmd.append("--skip-migrate")
    for name in image:
        cmd.extend(["--image", name])
    subprocess_run(cmd)
