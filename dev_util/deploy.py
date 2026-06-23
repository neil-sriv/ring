from __future__ import annotations

import os
from typing import Any

import click

from dev_util.compose import compose_starter
from dev_util.dev import dev_command, dev_group, subprocess_run
from dev_util.docker import push, tag
from dev_util.frontend import fe_build

DEFAULT_VITE_API_URL = "https://ring.neilsriv.tech"
DEFAULT_AWS_REGION = "us-east-1"
ECR_PUBLIC_REGISTRY = "public.ecr.aws"


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
def deploy_prod(
    ctx: click.Context,
    vite_api_url: str,
    maintenance_mode: bool,
    region: str,
    skip_fe_build: bool,
    skip_login: bool,
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
    if not skip_fe_build:
        ctx.invoke(fe_build)

    build_env = {
        **os.environ,
        "VITE_API_URL": vite_api_url,
        "VITE_MAINTENANCE_MODE": "true" if maintenance_mode else "false",
    }
    subprocess_run(compose_starter("prod") + ["build"], env=build_env)

    if not skip_login:
        _ecr_public_login(region)

    ctx.invoke(tag)
    ctx.invoke(push)
