from pathlib import Path

import pytest

import vurf.parser


def parse(filename):
    with open(Path(__file__).parent / filename) as f:
        return vurf.parser.parse(f)


@pytest.mark.parametrize(
    "filename",
    [
        "simple.vurf",
        "basic.vurf",
        "ellipses.vurf",
        "../vurf/defaults/packages.vurf",
        "quoted.vurf",
        "conditionals.vurf",
    ],
)
def test_parsing_without_rasing_errors(filename):
    parse(filename)
    assert True


def _get_packages(root, section, parameters):
    return " ".join(root.get_packages(section, parameters))


def _get_packages_from_file(filename, section, parameters):
    root = parse(filename)
    return _get_packages(root, section, parameters)


def test_ellipses():
    assert _get_packages_from_file("ellipses.vurf", None, {"x": True, "y": True}) == ""


def test_quotes():
    root = parse("quoted.vurf")
    assert root._children[0].children[0].data == "multi word package"
    assert _get_packages(root, None, {}) == "'multi word package'"


def test_remove():
    root = parse("simple.vurf")
    root.remove_package("paru", "package")
    assert _get_packages(root, None, {"sometest": True}) == ""
    root.add_package("paru", "package")
    assert _get_packages(root, None, {"sometest": False}) == "package"
    root.remove_package("paru", "package")
    assert _get_packages(root, None, {"sometest": False}) == ""


def test_has_child():
    root = parse("basic.vurf")
    formatted = root.to_string()
    assert root.has_package("pip", "package3")
    root.add_package("pip", "package3")  # already there
    assert root.to_string() == formatted
    root.add_package("pip", "package4")  # not there
    assert root.to_string() != formatted


def test_conditionals():
    root = parse("conditionals.vurf")
    section = root._children[0]
    basic = section.children[0]
    multi = section.children[1]
    function = section.children[2]
    assert basic.data == "basic == 0"
    assert multi.data == "one == 1 and something_else"
    assert function.data == "pathlib.Path('~/some-file').exists()"
