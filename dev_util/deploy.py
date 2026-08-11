from __future__ import annotations

import os
from typing import Any

import click

from dev_util.compose import compose_starter
from dev_util.dev import dev_command, dev_group, subprocess_run
from dev_util.docker import push, tag

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
    "--region",
    type=str,
    default=DEFAULT_AWS_REGION,
    show_default=True,
    help="AWS region used for the public ECR login.",
)
@click.option(
    "--skip-login",
    is_flag=True,
    default=False,
    help="Skip the public ECR `docker login` step.",
)
def deploy_prod(
    ctx: click.Context,
    region: str,
    skip_login: bool,
    *args: list[Any],
    **kwargs: dict[Any, Any],
) -> None:
    """Build, tag, and push the production backend images to public ECR.

    The frontend is deployed by Cloudflare Workers Builds on merges to
    dev and is not part of this flow.

      1. compose --profile prod build
      2. aws ecr-public login -> docker login
      3. ring docker tp (tag + push)
    """
    subprocess_run(compose_starter("prod") + ["build"], env=dict(os.environ))

    if not skip_login:
        _ecr_public_login(region)

    ctx.invoke(tag)
    ctx.invoke(push)
