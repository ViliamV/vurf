#!/usr/bin/env python
"""
This is WIP!
"""
import re

from collections import defaultdict
from itertools import chain
from pathlib import Path

from vurf import Vurf


Section = str
Package = str

Packages = defaultdict[Section, set[Package]]

translation = {"brew": ["shared", "brew"]}


def brewfile_reader(filename: str) -> Packages:
    packages = defaultdict(set)
    with Path(filename).open() as brewfile:
        for line in brewfile:
            section, name = line.strip().split(maxsplit=1)
            if section == "mas":
                match = re.findall(r"id: (\d+)", name)
                if match:
                    name = match[0]
            else:
                if " " not in name and name.startswith('"'):
                    name = name.strip('"')
            packages[section].add(name)
    return packages


def processor(packages: Packages) -> None:
    vurf = Vurf()
    for section, brew_packages in packages.items():
        vurf_sections = translation.get(section, [section])
        vurf_packages = set(chain.from_iterable((vurf.packages(s) for s in vurf_sections)))
        missing_in_vurf = brew_packages - vurf_packages
        missing_in_brewfile = vurf_packages - brew_packages
        print(f"{section=}\n{missing_in_vurf=}\n{missing_in_brewfile=}\n")


if __name__ == "__main__":
    processor(brewfile_reader("../../Brewfile"))
