# ruff: noqa: F401
# pyright: reportUnusedImport=false
# flake8: noqa: F401

from typing import Any

from ring.api_identifier import util as api_identifier_crud
from ring.letters.crud import letter as letter_crud
from ring.letters.crud import question as question_crud
from ring.parties.crud import group as group_crud
from ring.parties.crud import user as user_crud
from ring.scripts.script_base import script_di
from ring.sqlalchemy_base import Session
from ring.tasks.crud import schedule as schedule_crud


def _autoreload():
    for extension in ["autoreload", "pprintpp", "ipython_autoimport"]:
        get_ipython().run_line_magic("load_ext", extension)  # type: ignore # noqa: F821
    get_ipython().run_line_magic("autoreload", "2")  # type: ignore  # noqa: F821
    return "Autoreload enabled"


@script_di()
def run_script(db: Session) -> None:
    # import ring.postgres_models
    import click
    import sqlalchemy
    from IPython import embed  # type: ignore  # type: ignore
    from traitlets.config import Config

    import ring
    from ring.letters.models.default_question_model import DefaultQuestion
    from ring.letters.models.letter_model import Letter
    from ring.letters.models.question_model import Question
    from ring.letters.models.response_model import Response
    from ring.lib.util import get_all_subclasses
    from ring.notifications.models.subscription import Subscription
    from ring.parties.models.group_model import Group
    from ring.parties.models.invite_model import Invite
    from ring.parties.models.user_model import User
    from ring.sqlalchemy_base import Base
    from ring.tasks.crud import (
        task as task_crud,
    )
    from ring.tasks.models.schedule_model import Schedule
    from ring.tasks.models.task_model import Task

    click.echo("Configuring IPython...")
    c = Config()
    context: dict[str, Any] = {
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
