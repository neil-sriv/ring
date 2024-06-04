import click
from IPython import embed
from traitlets.config import Config
from ring.sqlalchemy_base import Session
from ring.scripts.script_base import script_di
from ring.postgres_models import *  # noqa: F401, F403
from sqlalchemy import select  # noqa: F401


@script_di()
def run_script(db: Session) -> None:
    click.echo("Configuring IPython...")
    c = Config()
    c.InteractiveShellEmbed.colors = "Neutral"
    embed(colors="Neutral", config=c)
