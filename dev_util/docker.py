from __future__ import annotations

import click

from dev_util.dev import dev_command, dev_group, subprocess_run

ECR_URI_BASE = "public.ecr.aws/z2k1e8p1/"

IMAGE_TAG_NAMES = [
    "ring-api",
    "ring-llm",
]

# Compose service names for images built via compose.core + compose.prod.
COMPOSE_SERVICE_BY_IMAGE = {
    "ring-api": "api",
}


@dev_group("docker")
@click.pass_context
def docker(ctx: click.Context) -> None:
    pass


def _ecr_refs(image: str, extra_tags: tuple[str, ...] = ()) -> list[str]:
    refs = [f"{ECR_URI_BASE}{image}:latest"]
    for extra in extra_tags:
        if not extra or extra == "latest":
            continue
        refs.append(f"{ECR_URI_BASE}{image}:{extra}")
    return refs


@dev_command("tag", docker)
@click.option(
    "--image",
    "-i",
    type=click.Choice(IMAGE_TAG_NAMES),
    multiple=True,
    default=IMAGE_TAG_NAMES,
)
@click.option(
    "--extra-tag",
    "-t",
    multiple=True,
    default=(),
    help="Additional image tag(s) besides :latest (e.g. git SHA).",
)
def tag(
    ctx: click.Context,
    image: list[str],
    extra_tag: tuple[str, ...],
) -> None:
    for name in image:
        for ref in _ecr_refs(name, extra_tag):
            subprocess_run(["docker", "tag", f"prod-{name}:latest", ref])


@dev_command("push", docker)
@click.option(
    "--image",
    "-i",
    type=click.Choice(IMAGE_TAG_NAMES),
    multiple=True,
    default=IMAGE_TAG_NAMES,
)
@click.option(
    "--extra-tag",
    "-t",
    multiple=True,
    default=(),
    help="Additional image tag(s) besides :latest (e.g. git SHA).",
)
def push(
    ctx: click.Context,
    image: list[str],
    extra_tag: tuple[str, ...],
) -> None:
    for name in image:
        for ref in _ecr_refs(name, extra_tag):
            subprocess_run(["docker", "push", ref])


@dev_command("tp", docker)
@click.option(
    "--image",
    "-i",
    type=click.Choice(IMAGE_TAG_NAMES),
    multiple=True,
    default=IMAGE_TAG_NAMES,
)
@click.option(
    "--extra-tag",
    "-t",
    multiple=True,
    default=(),
    help="Additional image tag(s) besides :latest (e.g. git SHA).",
)
def push_and_tag(
    ctx: click.Context,
    image: list[str],
    extra_tag: tuple[str, ...],
) -> None:
    ctx.invoke(tag, image=image, extra_tag=extra_tag)
    ctx.invoke(push, image=image, extra_tag=extra_tag)
