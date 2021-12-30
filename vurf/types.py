from dataclasses import dataclass
from typing import Union


@dataclass
class Section:
    name: str
    install: str = "echo No install command provided, packages:"
    uninstall: str = "echo No uninstall command provided, packages:"
    sequential: bool = False


Sections = dict[str, Section]
Parameters = dict[str, Union[str, int, float, bool]]


@dataclass
class Config:
    packages_location: str
    default_section: str
    sections: Sections
    parameters: Parameters
