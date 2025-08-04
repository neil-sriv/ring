"""Interactive shell for Ring development.

This module provides an enhanced IPython shell for Ring development with
auto-imports, auto-reloading, and access to common Ring components.
"""

# ruff: noqa: F401
# pyright: reportUnusedImport=false
# flake8: noqa: F401
from __future__ import annotations

from typing import Any

from ring.api_identifier import util as api_identifier_crud
from ring.fastapp.init_app_modules import init_offline_modules
from ring.letters.crud import letter as letter_crud
from ring.letters.crud import question as question_crud
from ring.parties.crud import group as group_crud
from ring.parties.crud import user as user_crud
from ring.scripts.script_base import script_di
from ring.sqlalchemy_base import Session
from ring.tasks.crud import schedule as schedule_crud


def _autoreload() -> str:
    """Configure IPython extensions for development.

    This function enables several IPython extensions that enhance the development
    experience:
    - autoreload: Automatically reloads modules when they change
    - pprintpp: Provides pretty printing for better output formatting
    - ipython_autoimport: Automatically imports commonly used modules

    Returns:
        str: Confirmation message indicating autoreload is enabled
    """
    for extension in ["autoreload", "pprintpp", "ipython_autoimport"]:
        get_ipython().run_line_magic("load_ext", extension)  # type: ignore # noqa: F821
    get_ipython().run_line_magic("autoreload", "2")  # type: ignore  # noqa: F821
    return "Autoreload enabled"


@script_di()
def run_script(db: Session) -> None:
    """Launch an enhanced IPython shell for Ring development.

    This function sets up an IPython shell with:
    - Auto-reloading of modules
    - Pre-imported Ring models and utilities
    - Database session
    - SQLAlchemy integration
    - Configured logging

    Args:
        db (Session): Database session provided by script_di
    """
    import click
    import sqlalchemy
    from IPython import embed
    from loguru import logger
    from traitlets.config import Config

    import ring
    from ring.lib.util import get_all_subclasses
    from ring.sqlalchemy_base import Base

    init_offline_modules()

    click.echo("Configuring IPython...")
    c = Config()
    context: dict[str, Any] = {
        "ring": ring,
        "db": db,
        "ar": _autoreload,
        "sa": sqlalchemy,
    }
    context.update({cls.__name__: cls for cls in get_all_subclasses(Base)})  # type: ignore
    c.InteractiveShellEmbed = c.TerminalInteractiveShell
    c.InteractiveShellEmbed.colors = "Neutral"
    c.InteractiveShellApp.exec_lines = [
        "ar()",
    ]
    embed(colors="Neutral", user_ns=context, config=c)

    logger.level("DEBUG")
    logger.debug("Debug logging enabled")
