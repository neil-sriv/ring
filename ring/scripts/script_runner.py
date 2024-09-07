import json
import click
import pathlib
import importlib.util
# import asyncio


@click.group()
def script():
    pass


@script.command()
@click.argument("script", type=click.Path(exists=True, path_type=pathlib.Path))
@click.option("--json-args", type=str, default="{}")
def run_script(script: pathlib.Path, json_args: str):
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
