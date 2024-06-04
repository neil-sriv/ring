from ring.scripts.script_base import script_di
from ring.sqlalchemy_base import Session


def _autoreload():
    for extension in ["autoreload", "pprintpp", "ipython_autoimport"]:
        get_ipython().run_line_magic("load_ext", extension)  # type: ignore # noqa: F821
    get_ipython().run_line_magic("autoreload", "2")  # type: ignore  # noqa: F821
    return "Autoreload enabled"


@script_di()
def run_script(db: Session) -> None:
    import ring.postgres_models
    import sqlalchemy
    import click
    from IPython import embed  # type: ignore
    from traitlets.config import Config
    import ring
    from ring.lib.util import get_all_subclasses
    from ring.sqlalchemy_base import Base

    click.echo("Configuring IPython...")
    c = Config()
    context = {
        "ring": ring,
        "db": db,
        "ar": _autoreload,
        "sqlalchemy": sqlalchemy,
    }
    context.update({cls.__name__: cls for cls in get_all_subclasses(Base)})  # type: ignore
    c.InteractiveShellEmbed = c.TerminalInteractiveShell
    c.InteractiveShellEmbed.colors = "Neutral"
    c.InteractiveShellApp.exec_lines = [
        "ar()",
    ]
    embed(colors="Neutral", user_ns=context, config=c)
