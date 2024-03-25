import click
from dev_util.dev import dev_command, dev_group, subprocess_run


ECR_URI_BASE = "public.ecr.aws/z2k1e8p1/"

IMAGE_TAG_NAMES = [
    "ring-worker",
    "ring-next",
    "ring-api",
    "ring-beat",
]


@dev_group("docker")
@click.pass_context
def docker(ctx: click.Context) -> None:
    pass


@dev_command("tag", docker)
@click.option(
    "--image",
    "-i",
    type=click.Choice(IMAGE_TAG_NAMES),
    multiple=True,
    default=IMAGE_TAG_NAMES,
)
def tag(image: list[str]) -> None:
    run_cmds = [
        ["docker", "tag", f"{i}:latest", f"{ECR_URI_BASE}{i}:latest"] for i in image
    ]
    for cmd in run_cmds:
        subprocess_run(cmd)


@dev_command("push", docker)
@click.option(
    "--image",
    "-i",
    type=click.Choice(IMAGE_TAG_NAMES),
    multiple=True,
    default=IMAGE_TAG_NAMES,
)
def push(image: list[str]) -> None:
    run_cmds = [["docker", "push", f"{ECR_URI_BASE}{i}:latest"] for i in image]
    for cmd in run_cmds:
        subprocess_run(cmd)


@dev_command("tp", docker)
@click.pass_context
def push_and_tag(ctx: click.Context) -> None:
    ctx.forward(tag)
    # ctx.invoke(tag)
    ctx.forward(push)
    # ctx.invoke(push)
