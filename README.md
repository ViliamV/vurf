# VURF
![forthebadge](https://forthebadge.com/images/badges/powered-by-black-magic.svg)

![forthebadge](https://forthebadge.com/images/badges/pretty-risque.svg)

![forthebadge](https://forthebadge.com/images/badges/works-on-my-machine.svg)

[![PyPI version](https://badge.fury.io/py/vurf.svg)](https://badge.fury.io/py/vurf)

> Viliam's Universal Requirements Format

## What it is
*VURF* is a format, parser, and CLI for saving packages into Python-ish looking file.

### Example packages.vurf
```python
with pip:
  vurf
  black
  if at_work:
    ql-cq
    ql-orange
with brew:
  nnn  # terminal file manager
```

### Usage
!TODO

## Grammar
*VURF* has [grammar](./vurf/grammar.lark) and LALR(1) parser implemented in [Lark](https://github.com/lark-parser/lark).
It aims to look like Python code as much as possible.

### Keywords
* `with [section]` - specifies "section" of requirements file. Different sections usually have different installers.
* `if [condition]:` - conditions for including packages. See [Conditions](##Conditions) sections.
* `elif [condition]:`
* `else:`
* `...` - ellipsis - placeholder for empty section.

### Packages
* are saved as `[name]  # [comment]`
* `name` can be almost any valid package name (cannot start with "." or contain tabs or newline characters)
* names containing spaces must be quoted. E.g. `'multi word package name'`
* comments are optional

## Config

Note: *VURF* will automatically create config file on the first run.

### Config file format
```toml
# Where packages file is saved
packages_location = "/Users/viliam/packages.vurf"
# Name of the default section
default_section = "brew"

# Sections can be though of as installers for different packages
# Value of the section is the command for installing packages with `vurf install`
[sections]
brew = "brew install"
cask = "brew install --cask"
python = "pip install --quiet --user"

# Parameters are constants that can be accessed from conditionals
[parameters]
hostname = "mac"
primary_computer = true
fs = "apfs"
```

## CLI
```
$ vurf
Usage: vurf [OPTIONS] COMMAND [ARGS]...

Options:
  -q, --quiet  Don't produce unnecessary output.
  --version    Show the version and exit.
  --help       Show this message and exit.

Commands:
  add       Add package(s).
  config    Edit config file.
  default   Print default section.
  edit      Edit packages file.
  format    Format packages file.
  has       Exit with indication if package is in packages.
  install   Install packages.
  packages  Print list of packages.
  print     Print contents of packages file.
  remove    Remove package(s).
  sections  Print list of sections.
```

## Conditions
!TODO

## Hooks
!TODO
