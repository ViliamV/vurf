import sys

from functools import wraps
from types import SimpleNamespace
from typing import Callable, Iterable, Optional

import click

from vurf.constants import APP_NAME, CONFIG_NAME
from vurf.lib import ensure_config, expand_path
from vurf.nodes import Root
from vurf.parser import parse
from vurf.types import Config


SECTION_ENV = f"{APP_NAME}_SECTION"


class HintedObject(SimpleNamespace):
    config: Config
    root: Root
    quit: bool


class HintedContext(SimpleNamespace):
    obj: HintedObject


defaul_section_option = click.option(
    "-s",
    "--section",
    required=False,
    envvar=SECTION_ENV,
    help=f"Defaults to `default_section` from config. Reads {SECTION_ENV} env variable.",
)
all_sections_option = click.option(
    "-s",
    "--section",
    required=False,
    envvar=SECTION_ENV,
    help=f"Defaults to all sections. Reads {SECTION_ENV} env variable.",
)
separator_option = click.option(
    "--separator",
    required=False,
    type=str,
    default="\n",
    help='Section separator. Defaults to "\\n".',
)


def write_packages(ctx: HintedContext):
    with expand_path(ctx.obj.config.packages_location).open("w") as f:
        f.write(ctx.obj.root.to_string())


def no_traceback(f: Callable) -> Callable:
    @wraps(f)
    def wrapper(*args, **kwds):
        try:
            return f(*args, **kwds)
        except Exception as e:
            args = " ".join(map(str, e.args))
            sys.stderr.write(f"Error: {args}\n")
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


# Root -> get_sections
@main.command(help="Print list of sections.")
@separator_option
@click.pass_context
@no_traceback
def sections(ctx: HintedContext, separator: str):
    click.echo(separator.join(ctx.obj.root.get_sections()))


# Root -> has_section
@main.command(help="Exit with indication if section is in sections.")
@click.argument("section")
@click.pass_context
@no_traceback
def has_section(ctx: HintedContext, section: str):
    sys.exit(int(not ctx.obj.root.has_section(section)))


# Root -> get_packages
@main.command(help="Print list of packages.")
@all_sections_option
@separator_option
@click.pass_context
@no_traceback
def packages(ctx: HintedContext, section: Optional[str], separator: str):
    click.echo(separator.join(ctx.obj.root.get_packages(section, ctx.obj.config.parameters)))


# Root -> has_package
@main.command(help="Exit with indication if package is in packages.")
@all_sections_option
@click.argument("package")
@click.pass_context
@no_traceback
def has(ctx: HintedContext, section: Optional[str], package: str):
    sys.exit(int(not ctx.obj.root.has_package(section, package)))


# Root -> get_package_section
@main.command(help="Print the first section that contains the package.")
@click.pass_context
@click.argument("package")
@no_traceback
def package_section(ctx: HintedContext, package: str):
    section = ctx.obj.root.get_package_section(package)
    if section is None:
        sys.exit(1)
    click.echo(section)


# Root -> add_package
@main.command(help="Add package(s).")
@defaul_section_option
@click.argument("packages", nargs=-1)
@click.pass_context
@no_traceback
def add(ctx: HintedContext, section: Optional[str], packages: Iterable[str]):
    if section is None:
        section = ctx.obj.config.default_section
    for package in packages:
        ctx.obj.root.add_package(section, package)
    write_packages(ctx)


# Root -> remove_package
@main.command(help="Remove package(s).")
@defaul_section_option
@click.argument("packages", nargs=-1)
@click.pass_context
@no_traceback
def remove(ctx: HintedContext, section: Optional[str], packages: Iterable[str]):
    if section is None:
        section = ctx.obj.config.default_section
    for package in packages:
        ctx.obj.root.remove_package(section, package)
    write_packages(ctx)


# Root -> install
@main.command(help="Install packages.")
@all_sections_option
@click.pass_context
@no_traceback
def install(ctx: HintedContext, section: Optional[str]):
    click.echo(ctx.obj.root.install(section, ctx.obj.config.sections, ctx.obj.config.parameters))


# Root -> uninstall
@main.command(help="Uninstall packages.")
@all_sections_option
@click.pass_context
@no_traceback
def uninstall(ctx: HintedContext, section: Optional[str]):
    click.echo(ctx.obj.root.uninstall(section, ctx.obj.config.sections, ctx.obj.config.parameters))


@main.command(help="Print default section.")
@click.pass_context
@no_traceback
def default(ctx):
    click.echo(ctx.obj.config.default_section)


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
