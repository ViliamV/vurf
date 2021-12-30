from pathlib import Path
from shutil import copyfile
from typing import Any

import click
import tomli

from vurf.constants import APP_NAME, CONFIG_NAME
from vurf.types import Config, Section


DEFAULTS_PATH = "defaults"
DEFAULT_PACKAGES_NAME = "packages.vurf"


def expand_path(filename: str) -> Path:
    path = Path(filename)
    if "~" in filename:
        path = path.expanduser()
    return path


def ensure_config(quiet: bool) -> Config:
    config_path = Path(click.get_app_dir(APP_NAME))
    if not config_path.exists():
        config_path.mkdir(parents=True)
    config_file = config_path / CONFIG_NAME
    default_packages_file = Path.home() / DEFAULT_PACKAGES_NAME
    if not config_file.is_file():
        if not quiet:
            click.secho("Config file not found...", fg="bright_black")
            click.secho(f"Creating default config {config_file}", fg="bright_black")
        copyfile(Path(__file__).parent / DEFAULTS_PATH / CONFIG_NAME, config_file)
    with config_file.open("rb") as opened:
        config = tomli.load(opened)
    if not expand_path(config["packages_location"]).is_file():
        if not quiet:
            click.secho("Packages file not found...", fg="bright_black")
            click.secho(f"Creating default {default_packages_file}", fg="bright_black")
            click.secho("You can change it later in the config.", fg="bright_black")
        copyfile(
            Path(__file__).parent / DEFAULTS_PATH / DEFAULT_PACKAGES_NAME,
            default_packages_file,
        )
    # Transform sections
    sections = {section["name"]: Section(**section) for section in config.pop("sections")}
    return Config(**config, sections=sections)
