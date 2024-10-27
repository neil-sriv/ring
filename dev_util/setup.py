import click
from dev_util.dev import dev_group, subprocess_run


@dev_group("setup")
@click.pass_context
def setup(ctx: click.Context) -> None:
    pass


@setup.command(name="requirements")
def fe_dev() -> None:
    subprocess_run(["uv", "sync"])
    subprocess_run(["pre-commit", "install"])
