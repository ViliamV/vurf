import functools
import operator
import os
import pathlib
import subprocess

from functools import cached_property, partial
from itertools import chain
from typing import Callable, Iterable, Optional, Union, cast

from vurf.types import Parameters, Sections


INDENT = "  "
COMMENT = "#"
ELLIPSIS = "..."
NEWLINE = "\n"


class Node:
    def __init__(self, data: str, children: Optional[list["Node"]] = None) -> None:
        self.data = data
        if children is None:
            children = []
        self.children = children

    def __str__(self) -> str:
        return self.data

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self.data == other.data

    def to_string(self, indent=0) -> str:
        indented = f"{INDENT * indent}{self}"
        return NEWLINE.join(chain((indented,), (child.to_string(indent + 1) for child in self.children)))

    def add_child(self, node: "Node", *indexes: int) -> None:
        if not indexes:
            # No duplication
            if self.has_child(node):
                return
            self.children.append(node)
        else:
            self.children[indexes[0]].add_child(node, *indexes[1:])

    def remove_child(self, node: "Node") -> None:
        if node in self.children:
            self.children = [child for child in self.children if child != node]
            # Add ellipsis to empty withs and ifs
            if isinstance(self, (With, If, Elif, Else)) and not self.children:
                self.add_child(Ellipsis_(ELLIPSIS))
        else:
            for child in self.children:
                child.remove_child(node)

    def has_child(self, node: "Node") -> bool:
        if node in self.children:
            return True
        return any(child.has_child(node) for child in self.children)

    def get_packages(self, parameters: Parameters) -> Iterable[str]:
        return chain.from_iterable(child.get_packages(parameters) for child in self.children)


class Comment(Node):
    @classmethod
    def from_parsed(cls, data) -> "Comment":
        return cls(data[0].value)


class Package(Node):
    def __init__(self, data: str, comment: Optional["Comment"] = None) -> None:
        if data[0] == data[-1] and data[0] in {'"', "'"}:
            self._quoted = True
            data = data[1:-1]
        elif " " in data:
            self._quoted = True
        else:
            self._quoted = False
        super().__init__(data)
        self._comment = comment

    @classmethod
    def from_parsed(cls, data) -> "Package":
        return cls(data[0].value, data[1] if len(data) > 1 else None)

    @property
    def package_name(self) -> str:
        if self._quoted:
            return f"'{super().__str__()}'"
        return super().__str__()

    def __str__(self) -> str:
        if self._comment:
            return f"{self.package_name}{INDENT}{self._comment}"
        return self.package_name

    def get_packages(self, _: Parameters) -> Iterable[str]:
        return [self.package_name]


class With(Node):
    @classmethod
    def from_parsed(cls, data) -> "With":
        arg, body = data
        return cls(arg.children[0].value, body.children)

    def __str__(self) -> str:
        return f"with {self.data}:"


class EvaluableMixin:
    data: str = "THIS IS FOR MIXIN TYPING TO WORK"

    def eval(self, parameters: Parameters) -> bool:
        return bool(eval(self.data, {"os": os, "pathlib": pathlib, "subprocess": subprocess}, parameters))


class If(Node, EvaluableMixin):
    def __init__(
        self,
        data: str,
        children: list["Node"],
        branches: Optional[list[Union["Elif", "Else"]]] = None,
    ) -> None:
        super().__init__(data, children=children)
        if branches is None:
            branches = []
        self.branches = branches

    def get_packages(self, parameters: Parameters) -> Iterable[str]:
        is_true = self.eval(parameters)
        packages = [super().get_packages(parameters)] if is_true else []
        for branch in self.branches:
            if isinstance(branch, Elif) and branch.eval(parameters):
                packages.append(branch.get_packages(parameters))
            if isinstance(branch, Else) and not is_true:
                packages.append(branch.get_packages(parameters))
        return chain.from_iterable(packages)

    @classmethod
    def from_parsed(cls, data) -> "If":
        arg, body = data[0], data[1]
        return cls(arg.children[0].value, body.children, data[2:])

    def __str__(self) -> str:
        return f"if {self.data}:"

    def to_string(self, indent=0) -> str:
        return NEWLINE.join(
            chain(
                (super().to_string(indent=indent),),
                (branch.to_string(indent) for branch in self.branches),
            )
        )


class Elif(Node, EvaluableMixin):
    @classmethod
    def from_parsed(cls, data) -> "Elif":
        arg, body = data
        return cls(arg.children[0].value, body.children)

    def __str__(self) -> str:
        return f"elif {self.data}:"


class Else(Node):
    @classmethod
    def from_parsed(cls, data) -> "Else":
        return cls("else:", data[0].children)


class Ellipsis_(Node):
    @classmethod
    def from_parsed(cls, data) -> "Ellipsis_":
        return cls(data[0].value)


class Root:
    """
    Public API

    # Sections
        * get_sections() -> Iterable[str]
        * has_section(str) -> bool
        * add_section(str) -> None
        * remove_section(str) -> None
    # Packages
        * get_packages(Optional[str], Parameters) -> Iterable[str]
        * has_package(Optional[str], str) -> bool
        * get_package_section(str) -> Optional[str]
        * add_package(str, str) -> None
        * remove_package(str, str) -> None
    # Commands
        * install(Optional[str], Sections, Parameters) -> None
        * uninstall(Optional[str], Sections, Parameters) -> None

    """

    def __init__(self, children: Optional[list["Node"]] = None) -> None:
        if children is None:
            children = []
        self._children = children
        self.install = partial(self._exec, operator.attrgetter("install"))
        self.uninstall = partial(self._exec, operator.attrgetter("uninstall"))

    @classmethod
    def from_parsed(cls, data) -> "Root":
        return cls(data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}"

    def to_string(self, indent=0) -> str:
        return NEWLINE.join(child.to_string(indent) for child in self._children) + NEWLINE

    @property
    def _sections(self) -> dict[str, With]:
        return {child.data: child for child in self._children if isinstance(child, With)}

    def _package(self, package_name: str) -> Package:
        if COMMENT in package_name:
            index = package_name.index(COMMENT)
            name = package_name[:index]
            comment = Comment(package_name[index:])
        else:
            name = package_name
            comment = None
        return Package(name.strip(), comment)

    def get_sections(self) -> Iterable[str]:
        return self._sections.keys()

    def has_section(self, section_name: str) -> bool:
        return section_name in self._sections

    def add_section(self, section_name: str) -> None:
        self._children.append(With(section_name, [Ellipsis_(ELLIPSIS)]))

    def remove_section(self, section_name: str) -> None:
        self._children.remove(With(section_name))

    def get_packages(self, section_name: Optional[str], parameters: Parameters) -> Iterable[str]:
        if section_name is not None:
            return self._sections[section_name].get_packages(parameters)
        else:
            return chain.from_iterable(
                section.get_packages(parameters) for section in self._sections.values()
            )

    def has_package(self, section_name: Optional[str], package_name: str) -> bool:
        package = self._package(package_name)
        if section_name is not None:
            return self._sections[section_name].has_child(package)
        else:
            return any(section.has_child(package) for section in self._sections.values())

    def get_package_section(self, package_name: str) -> Optional[str]:
        package = self._package(package_name)
        for section_name, section in self._sections.items():
            if section.has_child(package):
                return section_name
        return None

    def add_package(self, section_name: str, package_name: str, *indexes: int) -> None:
        """
        Note: AFAIK `indexes` are unused
        but can be used to add packages to different sub-sections (if/else) inside section
        """
        package = self._package(package_name)
        self._sections[section_name].add_child(package, *indexes)

    def remove_package(self, section_name: str, package_name: str) -> None:
        package = self._package(package_name)
        self._sections[section_name].remove_child(package)

    def _exec(
        self,
        get_command: Callable[..., str],
        section_name: Optional[str],
        sections: Sections,
        parameters: Parameters,
    ) -> None:
        if section_name is not None:
            packages = self._sections[section_name].get_packages(parameters)
            command = get_command(sections[section_name])
            if sections[section_name].sequential:
                for package in packages:
                    subprocess.run(f"{command} {package}", shell=True)
            else:
                subprocess.run(f"{command} {' '.join(packages)}", shell=True)
            return
        else:
            for section in self._sections:
                self._exec(get_command, section, sections, parameters)
