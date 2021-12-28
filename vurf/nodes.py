import os
import pathlib
import subprocess
from functools import cached_property
from itertools import chain
from typing import Any, Iterable, Optional, Tuple, Union, cast


class Node:
    INDENT = "  "

    def __init__(self, data: str, children: list["Node"] = []) -> None:
        self.data = data
        self.children = children

    def __str__(self) -> str:
        return self.data

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self.data == other.data

    def to_string(self, indent=0) -> str:
        indented = f"{self.INDENT * indent}{self}"
        return "\n".join(
            chain((indented,), (child.to_string(indent + 1) for child in self.children))
        )

    def add_child(self, pkg: "Node", *indexes: int) -> None:
        if not indexes:
            self.children.append(pkg)
        else:
            self.children[indexes[0]].add_child(pkg, *indexes[1:])

    def remove_child(self, node: "Node") -> None:
        self.children = [child for child in self.children if child != node]
        for child in self.children:
            child.remove_child(node)
            # Add ellipsis to empty withs and ifs
            if isinstance(child, (With, If, Elif, Else)) and not child.children:
                child.add_child(Ellipsis_("..."))

    def has_child(self, node: "Node") -> bool:
        if any(child == node for child in self.children):
            return True
        return any(child.has_child(node) for child in self.children)

    def get_packages(self, separator: str) -> str:
        return separator.join(
            child.package_name for child in self.children if isinstance(child, Package)
        ).strip(separator)


class Comment(Node):
    @classmethod
    def from_parsed(cls, data) -> "Comment":
        return cls(data[0].value)


class Package(Node):
    def __init__(self, data: str, comment: Optional["Comment"] = None) -> None:
        if data[0] == data[-1] and data[0] in {'"', "'"}:
            self._quoted = True
            data = data[1:-1]
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
            return f"{self.package_name}{self.INDENT}{self._comment}"
        return self.package_name


class With(Node):
    @classmethod
    def from_parsed(cls, data) -> "With":
        arg, body = data
        return cls(arg.children[0].value, body.children)

    def __str__(self) -> str:
        return f"with {self.data}:"

    def get_packages(self, separator: str, parameters: dict[str, Any]) -> str:
        packages = [super().get_packages(separator)]
        for child in self.children:
            if isinstance(child, If):
                packages.append(child.get_packages(separator, parameters))
        return separator.join(packages).strip(separator)


class EvaluableMixin:
    def eval(self, parameters: dict[str, Any]) -> bool:
        return bool(eval(self.data, {"os": os, "pathlib": pathlib}, parameters))


class If(Node, EvaluableMixin):
    def __init__(
        self,
        data: str,
        children: list["Node"],
        branches: list[Union["Elif", "Else"]] = [],
    ) -> None:
        super().__init__(data, children=children)
        self.branches = branches

    def get_packages(self, separator: str, parameters: dict[str, Any]) -> str:
        self_is_true = self.eval(parameters)
        packages = [super().get_packages(separator)] if self_is_true else []
        for branch in self.branches:
            if isinstance(branch, Elif) and branch.eval(parameters):
                packages.append(branch.get_packages(separator))
            if isinstance(branch, Else) and not self_is_true:
                packages.append(branch.get_packages(separator))
        return separator.join(packages)

    @classmethod
    def from_parsed(cls, data) -> "If":
        arg, body = data[0], data[1]
        return cls(arg.children[0].value, body.children, data[2:])

    def __str__(self) -> str:
        return f"if {self.data}:"

    def to_string(self, indent=0) -> str:
        return "\n".join(
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
    def __init__(self, children: list["Node"] = []) -> None:
        self.children = children

    @classmethod
    def from_parsed(cls, data) -> "Root":
        return cls(data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}"

    def to_string(self, indent=0) -> str:
        return "\n".join(child.to_string(indent) for child in self.children) + "\n"

    @cached_property
    def section_indexes(self) -> dict[str, int]:
        return {
            child.data: i
            for i, child in enumerate(self.children)
            if isinstance(child, With)
        }

    def _get_section_by_name(self, section_name: str) -> "With":
        try:
            return cast(With, self.children[self.section_indexes[section_name]])
        except KeyError:
            raise KeyError(f'No section named "{section_name}"')

    def get_sections(self, separator: str) -> str:
        return separator.join(self.section_indexes.keys())

    def add_package(self, section_name: str, package_name: str, *indexes: int) -> None:
        section = self._get_section_by_name(section_name)
        args = package_name.split(maxsplit=1)
        comment = Comment(args[1].strip()) if len(args) > 1 else None
        package = Package(args[0].strip(), comment)
        # Ensure no duplicates
        if not section.has_child(package):
            section.add_child(package, *indexes)

    def has_package(self, section_name: str, package_name: str) -> bool:
        section = self._get_section_by_name(section_name)
        args = package_name.split(maxsplit=1)
        comment = Comment(args[1].strip()) if len(args) > 1 else None
        package = Package(args[0].strip(), comment)
        return section.has_child(package)

    def get_packages(
        self, section: Optional[str], parameters: dict[str, Any], separator: str
    ) -> str:
        if section is not None:
            return self._get_section_by_name(section).get_packages(
                separator, parameters
            )
        return separator.join(
            self.get_packages(section, parameters, separator)
            for section in self.section_indexes.keys()
        )

    def install(
        self,
        section: Optional[str],
        section_commands: dict[str, str],
        parameters: dict[str, Any],
    ) -> None:
        if section is not None:
            packages = self._get_section_by_name(section).get_packages(" ", parameters)
            command = section_commands[section]
            subprocess.run(f"{command} {packages}", shell=True)
            return
        for section in self.section_indexes.keys():
            self.install(section, section_commands, parameters)

    def remove_package(self, section: str, package: str) -> None:
        self._get_section_by_name(section).remove_child(Package(package))
