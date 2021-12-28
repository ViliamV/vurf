import sys
from functools import wraps
from types import SimpleNamespace
from typing import Callable, Iterable, Optional

import click

from vurf.constants import APP_NAME, CONFIG_NAME
from vurf.lib import ensure_config, expand_path
from vurf.parser import parse

SECTION_ENV = f"{APP_NAME}_SECTION"


section_option = click.option(
    "-s",
    "--section",
    required=False,
    envvar=SECTION_ENV,
    help=f"Defaults to `default_section` from config. Reads {SECTION_ENV} env variable.",
)


def write_packages(ctx):
    with expand_path(ctx.obj.config.packages_location).open("w") as f:
        f.write(ctx.obj.root.to_string())


def no_traceback(f: Callable) -> Callable:
    @wraps(f)
    def wrapper(*args, **kwds):
        try:
            return f(*args, **kwds)
        except Exception as e:
            sys.stderr.write(" ".join(map(str, e.args)) + "\n")
            sys.exit(1)

    return wrapper


@click.group()
@click.pass_context
@click.option("-q", "--quiet", is_flag=True, help="Don't produce unnecessary output.")
@click.version_option(package_name=APP_NAME.lower())
@no_traceback
def main(ctx, quiet):
    config = ensure_config(quiet)
    with expand_path(config.packages_location).open() as f:
        root = parse(f)
    ctx.obj = ctx.ensure_object(SimpleNamespace)
    ctx.obj.config = config
    ctx.obj.root = root
    ctx.obj.quiet = quiet


@main.command(help="Add package(s).")
@section_option
@click.argument("packages", nargs=-1)
@click.pass_context
@no_traceback
def add(ctx, section: Optional[str], packages: Iterable[str]):
    if section is None:
        section = ctx.obj.config.default_section
    for package in packages:
        ctx.obj.root.add_package(section, package)
    write_packages(ctx)


@main.command(help="Remove package(s).")
@section_option
@click.argument("packages", nargs=-1)
@click.pass_context
@no_traceback
def remove(ctx, section: Optional[str], packages: Iterable[str]):
    if section is None:
        section = ctx.obj.config.default_section
    for package in packages:
        ctx.obj.root.remove_package(section, package)
    write_packages(ctx)


@main.command(help="Print default section.")
@click.pass_context
@no_traceback
def default(ctx):
    click.echo(ctx.obj.config.default_section)


@main.command(help="Exit with indication if package is in packages.")
@section_option
@click.argument("package")
@click.pass_context
@no_traceback
def has(ctx, section: Optional[str], package: str):
    if section is None:
        section = ctx.obj.config.default_section
    sys.exit(int(not ctx.obj.root.has_package(section, package)))


@main.command(help="Print list of packages.")
@section_option
@click.option(
    "--separator",
    required=False,
    type=str,
    default="\n",
    help='Section separator. Defaults to "\\n".',
)
@click.pass_context
@no_traceback
def packages(ctx, section, separator):
    click.echo(separator.join(ctx.obj.root.get_packages(section, ctx.obj.config.parameters)))


@main.command(help="Print list of sections.")
@click.option(
    "--separator",
    required=False,
    type=str,
    default="\n",
    help='Section separator. Defaults to "\\n".',
)
@click.pass_context
@no_traceback
def sections(ctx, separator):
    click.echo(separator.join(ctx.obj.root.get_sections()))


@main.command(help="Install packages.")
@section_option
@click.pass_context
@no_traceback
def install(ctx, section):
    click.echo(ctx.obj.root.install(section, ctx.obj.config.sections, ctx.obj.config.parameters))


@main.command(name="print", help="Print contents of packages file.")
@click.pass_context
@no_traceback
def print_(ctx):
    click.echo_via_pager(ctx.obj.root.to_string())


@main.command(help="Format packages file.")
@click.pass_context
@no_traceback
def format(ctx):
    write_packages(ctx)


@main.command(help="Edit packages file.")
@click.pass_context
@no_traceback
def edit(ctx):
    click.edit(filename=str(expand_path(ctx.obj.config.packages_location)))


@main.command(help="Edit config file.")
@no_traceback
def config():
    click.edit(filename=f"{click.get_app_dir(APP_NAME)}/{CONFIG_NAME}")


if __name__ == "__main__":
    main()
