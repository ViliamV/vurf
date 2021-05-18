from functools import cached_property
from itertools import chain
from typing import Iterable, Optional, Tuple, Union, cast


class Node:
    INDENT = "  "

    def __init__(self, data: str, children: list["Node"] = []) -> None:
        self.data = data
        self.children = children

    def __str__(self) -> str:
        return self.data

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self})"

    def to_string(self, indent=0) -> str:
        indented = f"{self.INDENT * indent}{self}"
        return "\n".join(
            chain((indented,), (child.to_string(indent + 1) for child in self.children))
        )

    def add_package(self, pkg: "Package", *indexes: int) -> None:
        if not self.children:
            raise IndexError()
        if not indexes:
            self.children.append(pkg)
        else:
            self.children[indexes[0]].add_package(pkg, *indexes[1:])

    def children_with_children(self) -> Iterable[Tuple[int, "Node"]]:
        return (pair for pair in enumerate(self.children) if pair[1].children)


class Comment(Node):
    @classmethod
    def from_parsed(cls, data) -> "Comment":
        return cls(data[0].value)


class Package(Node):
    def __init__(self, data: str, comment: Optional["Comment"] = None) -> None:
        super().__init__(data)
        self._comment = comment

    @classmethod
    def from_parsed(cls, data) -> "Package":
        return cls(data[0].value, data[1] if len(data) > 1 else None)

    def __str__(self) -> str:
        if self._comment:
            return f"{self.data}{self.INDENT}{self._comment}"
        return super().__str__()


class With(Node):
    @classmethod
    def from_parsed(cls, data) -> "With":
        arg, body = data
        return cls(arg.children[0].value, body.children)

    def __str__(self) -> str:
        return f"with {self.data}:"

    @property
    def packages(self) -> str:
        # TODO: make Ifs work
        return " ".join(
            child.data for child in self.children if isinstance(child, Package)
        )


class If(Node):
    def __init__(
        self,
        data: str,
        children: list["Node"],
        branches: list[Union["Elif", "Else"]] = [],
    ) -> None:
        super().__init__(data, children=children)
        self.branches = branches

    def eval(self):
        return True

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


class Elif(Node):
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

    def _get_section_by_name(self, section: str) -> "With":
        return cast(With, self.children[self.section_indexes[section]])

    def add_package(self, package: "Package", section: str, *indexes: int) -> None:
        self._get_section_by_name(section).add_package(package, *indexes)

    def get_packages(self, section: Optional[str]) -> str:
        if section is not None:
            return self._get_section_by_name(section).packages
        return " ".join(
            self.get_packages(section) for section in self.section_indexes.keys()
        )
