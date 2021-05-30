from pathlib import Path
import vurf.parser
import pytest


def parse(filename):
    with open(Path(__file__).parent / filename) as f:
        return vurf.parser.parse(f)


@pytest.mark.parametrize(
    "filename",
    [
        "simple.vurf",
        "basic.vurf",
        "ellipses.vurf",
        "../vurf/default.vurf",
        "quoted.vurf",
    ],
)
def test_parsing_without_rasing_errors(filename):
    parse(filename)
    assert True


def test_ellipses():
    root = parse("ellipses.vurf")
    assert root.get_packages(None, {"x": True, "y": True}) == ""


def test_quotes():
    root = parse("quoted.vurf")
    assert root.children[0].children[0].data == "multi word package"
    assert root.get_packages(None, {}) == "'multi word package'"


def test_remove():
    root = parse("simple.vurf")
    root.remove_package("paru", "package")
    assert root.get_packages(None, {"sometest": True}) == ""
    root.add_package("paru", "package")
    assert root.get_packages(None, {"sometest": False}) == "package"
    root.remove_package("paru", "package")
    assert root.get_packages(None, {"sometest": False}) == ""
