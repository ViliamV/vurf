from typing import Iterable, Optional
from types import SimpleNamespace
import click
from vurf.parser import parse
from pathlib import Path
import toml
from shutil import copyfile


APP_NAME = "VURF"
CONFIG_NAME = "config.toml"
PACKAGES_NAME = "packages.vurf"


def ensure_config(quiet):
    config_path = Path(click.get_app_dir(APP_NAME))
    if not config_path.exists():
        config_path.mkdir(parents=True)
    config_file = config_path / CONFIG_NAME
    default_packages_file = Path.home() / PACKAGES_NAME
    if not config_file.is_file():
        if not quiet:
            click.secho("Config file not found...", fg="bright_black")
            click.secho(f"Creating default config {config_file}", fg="bright_black")
        copyfile(Path(__file__).parent / "config.toml", config_file)
    config = toml.load(config_file)
    if not Path(config["packages_location"]).is_file():
        if not quiet:
            click.secho("Packages file not found...", fg="bright_black")
            click.secho(f"Creating default {default_packages_file}", fg="bright_black")
            click.secho("You can change it later in the config.", fg="bright_black")
        copyfile(Path(__file__).parent / "default.vurf", default_packages_file)
    return config


def write_packages(ctx):
    with open(ctx.obj.config["packages_location"], "w") as f:
        f.write(ctx.obj.root.to_string())


@click.group()
@click.pass_context
@click.option("-q", "--quiet", is_flag=True, help="Don't produce unnecessary output.")
def main(ctx, quiet):
    config = ensure_config(quiet)
    with open(Path(config["packages_location"])) as f:
        root = parse(f)
    ctx.obj = ctx.ensure_object(SimpleNamespace)
    ctx.obj.config = config
    ctx.obj.root = root
    ctx.obj.quiet = quiet


@main.command(help="Add `package(s)` into a `section`.")
@click.option(
    "-s",
    "--section",
    required=False,
    envvar=f"{APP_NAME}_SECTION",
    help=f"Defaults to `default_section` from config. Reads {APP_NAME}_SECTION env variable.",
)
@click.argument("packages", nargs=-1)
@click.pass_context
def add(ctx, section: Optional[str], packages: Iterable[str]):
    if section is None:
        section = ctx.obj.config["default_section"]
    for package in packages:
        ctx.obj.root.add_package(section, package)
    write_packages(ctx)


@main.command(help="Print space separated packages.")
@click.option(
    "-s",
    "--section",
    required=False,
    envvar=f"{APP_NAME}_SECTION",
    help=f"Defaults to all. Reads {APP_NAME}_SECTION env variable.",
)
@click.pass_context
def packages(ctx, section):
    click.echo(ctx.obj.root.get_packages(section, ctx.obj.config["parameters"]))


@main.command(help="Install packages.")
@click.option(
    "-s",
    "--section",
    required=False,
    envvar=f"{APP_NAME}_SECTION",
    help=f"Defaults to all. Reads {APP_NAME}_SECTION env variable.",
)
@click.pass_context
def install(ctx, section):
    click.echo(
        ctx.obj.root.install(
            section, ctx.obj.config["sections"], ctx.obj.config["parameters"]
        )
    )


@main.command(name="print", help="Print contents of packages file.")
@click.pass_context
def print_(ctx):
    click.echo_via_pager(ctx.obj.root.to_string())


@main.command(help="Format packages file.")
@click.pass_context
def format(ctx):
    write_packages(ctx)


@main.command(help="Edit packages file.")
@click.pass_context
def edit(ctx):
    click.edit(filename=ctx.obj.config["packages_location"])


@main.command(help="Edit config.toml file.")
def config():
    click.edit(filename=f"{click.get_app_dir(APP_NAME)}/{CONFIG_NAME}")


if __name__ == "__main__":
    main()
