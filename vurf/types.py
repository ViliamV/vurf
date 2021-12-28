from dataclasses import dataclass
from typing import Union

Sections = dict[str, str]
Parameters = dict[str, Union[str, int, float, bool]]


@dataclass
class Config:
    packages_location: str
    default_section: str
    sections: Sections
    parameters: Parameters
