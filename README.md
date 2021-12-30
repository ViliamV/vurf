# VURF
![forthebadge](https://forthebadge.com/images/badges/powered-by-black-magic.svg)

![forthebadge](https://forthebadge.com/images/badges/pretty-risque.svg)

![forthebadge](https://forthebadge.com/images/badges/works-on-my-machine.svg)

[![PyPI version](https://badge.fury.io/py/vurf.svg)](https://badge.fury.io/py/vurf)

> Viliam's Universal Requirements Format

## What it is
*VURF* is a format, parser, CLI, and python module for saving packages into Python-ish looking file.
It supports different *sections*, *conditionals* and deep nesting and envaluation thanks to AST parser.

### Example packages.vurf
```python
with pip:
  vurf
  black
  click==8.0.0
  if at_work:
    ql-cq
    ql-orange
with brew:
  nnn  # terminal file manager
```

## Installation
```sh
pip install vurf
```

## Usage
```sh
# Do something to initialize config and packages files
$ vurf default

# Basic operations
$ vurf add some-package
$ vurf remove package

# Print packages
$ vurf packages

# Install them
$ vurf install
```

For all options look at [CLI](#CLI) section and for integration with other tools look at [Automation](./automation/).

## CLI
```
$ vurf
Usage: vurf [OPTIONS] COMMAND [ARGS]...

Options:
  -q, --quiet  Don't produce unnecessary output.
  --version    Show the version and exit.
  --help       Show this message and exit.

Commands:
  add              Add package(s).
  config           Edit config file.
  default          Print default section.
  edit             Edit packages file.
  format           Format packages file.
  has              Exit with indication if package is in packages.
  has-section      Exit with indication if section is in sections.
  install          Install packages.
  package-section  Print the first section that contains the package.
  packages         Print list of packages.
  print            Print contents of packages file.
  remove           Remove package(s).
  sections         Print list of sections.
  uninstall        Uninstall packages.
```

### Completions
Shell completions are installed into `vurf_completions` in your `side-packages`.
The easiest way to find the location is to run `pip show -f vurf | grep Location`.

Then you can source them for example like this
```bash
# .bashrc
source "/Users/viliam/Library/Python/3.10/lib/python/site-packages/vurf_completions/completions.bash"
```

## Config

Note: *VURF* will automatically create config file on the first run.

### Config file format
```toml
# Where packages file is saved
packages_location = "/Users/viliam/packages.vurf"
# Name of the default section
default_section = "brew"

# Sections can be though of as installers for different packages
# `install` and `uninstall` attributes are optional and default to `echo`
# `sequential` attribute is optional and defaults to `false`
# Use `sequential = true` if you want to install/uninstall packages one by one
[[sections]]
name = "brew"
install = "brew install"
uninstall = "brew uninstall"
sequential = false

[[sections]]
name = "cask"
install = "brew install --cask"

[[sections]]
name = "python"
install = "pip install --quiet --user"
uninstall = "pip uninstall"

# Parameters are constants that can be accessed from conditionals
[parameters]
hostname = "mac"
primary_computer = true
fs = "apfs"
```

## Grammar
*VURF* has [grammar](./vurf/parser/grammar.lark) and LALR(1) parser implemented in [Lark](https://github.com/lark-parser/lark).
The "source code" aims to look like Python code as much as possible.

### Keywords
* `with [section]` - specifies "section" of requirements file. Different sections usually have different installers.
* `if [condition]:` - conditions for including packages. See [Conditionals](##Conditionals) sections.
* `elif [condition]:`
* `else:`
* `...` - ellipsis - placeholder for empty section.

### Packages
* are saved as `[name]  # [comment]`
* `name` can be almost any valid package name (cannot start with "." or contain tabs or newline characters)
* names containing spaces must be quoted. E.g. `'multi word package name'`
* comments are optional

## Conditionals
Conditionals are evaluated using Python's `eval` function.
They can be as simple as 

```python
if var:
  ...
```

or as complex as

```python
if pathlib.Path('some-file').exists() and os.lstat('some-file').st_mode == 33188:
  ...
```

Evaluation has access to standard library modules:
* [os](https://docs.python.org/3/library/os.html)
* [pathlib](https://docs.python.org/3/library/pathlib.html)
* [subprocess](https://docs.python.org/3/library/subprocess.html)

and also to configuration variables defined in `config.toml`.

## Module
*VURF* provides python module that exposes approximately the same API as the CLI.

### Example
```python
from vurf import Vurf

with Vurf.context() as packages:
    sections = packages.sections()
    packages.add('some-package', section = sections[1])
    assert packages.has('some-package')
    packages.remove(['other-package', 'third-package'])
```
