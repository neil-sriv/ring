import click
import pathlib
import importlib.util
# import asyncio


@click.group()
def script():
    pass


@script.command()
@click.argument("script", type=click.Path(exists=True, path_type=pathlib.Path))
def run_script(script: pathlib.Path):
    file_name = script.name
    spec = importlib.util.spec_from_file_location(file_name, script)
    if spec is None:
        raise click.ClickException("Invalid script")
    module = importlib.util.module_from_spec(spec)
    # sys.modules[module.__name__] = module
    loader = spec.loader
    if loader is None:
        raise click.ClickException("Invalid script")
    loader.exec_module(module)
    click.echo(f"Running script: {module}")
    module.run_script()
    # asyncio.run(module.run_script())
    # subprocess.run(["python", str(script)])


if __name__ == "__main__":
    script()
