"""CLI tool for running Ring scripts.

This module provides a command-line interface for running Python scripts
with the Ring framework's dependencies and configuration.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib

import click

from ring.fastapp.init_app_modules import init_app_modules
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
    init_app_modules()

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
