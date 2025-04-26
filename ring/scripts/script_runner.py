"""CLI tool for running Ring scripts.

This module provides a command-line interface for running Python scripts
with the Ring framework's dependencies and configuration.
"""

import importlib.util
import json
import pathlib

import click

from ring.lib.logger import logger

# import asyncio


@click.group()
def script():
    """Ring script runner CLI tool.

    This command group provides functionality for running Ring scripts with
    proper dependency injection and configuration. It supports running scripts
    with optional JSON arguments.
    """
    pass


@script.command()
@click.argument("script", type=click.Path(exists=True, path_type=pathlib.Path))
@click.option("--json-args", type=str, default="{}")
def run_script(script: pathlib.Path, json_args: str):
    """Run a Ring script with optional JSON arguments.

    Args:
        script (pathlib.Path): Path to the script file to run
        json_args (str): JSON string containing arguments for the script

    Raises:
        click.ClickException: If the script file is invalid or cannot be loaded
    """
    import ring
    from ring.letters.models.default_question_model import DefaultQuestion
    from ring.letters.models.letter_model import Letter
    from ring.letters.models.question_model import Question
    from ring.letters.models.response_model import Response
    from ring.lib.logger import logger
    from ring.lib.util import get_all_subclasses
    from ring.notifications.models.subscription import Subscription
    from ring.parties.models.group_key_value import GroupKeyValue
    from ring.parties.models.group_model import Group
    from ring.parties.models.invite_model import Invite
    from ring.parties.models.user_model import User
    from ring.sqlalchemy_base import Base
    from ring.tasks.crud import (
        task as task_crud,
    )
    from ring.tasks.models.schedule_model import Schedule
    from ring.tasks.models.task_model import Task

    logger.level("DEBUG")
    logger.debug("Debug logging enabled")
    file_name = script.name
    spec = importlib.util.spec_from_file_location(file_name, script)
    if spec is None:
        raise click.ClickException("Invalid script")
    module = importlib.util.module_from_spec(spec)
    loader = spec.loader
    if loader is None:
        raise click.ClickException("Invalid script")

    script_args = json.loads(json_args)
    loader.exec_module(module)
    click.echo(f"Running script: {module}")
    module.run_script(**script_args)


if __name__ == "__main__":
    script()
