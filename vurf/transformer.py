from typing import Optional, Union
from lark import Transformer


class Node:
    INDENT = "  "

    def __init__(self, data: Optional[str], children: list["Node"] = []) -> None:
        self._data = data
        self._children = children

    def __str__(self) -> str:
        return str(self._data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self})"

    def to_string(self, indent=0) -> str:
        indented = f"{self.INDENT * indent}{self}"
        if not self._children:
            return indented
        return "\n".join(
            [indented] + [child.to_string(indent + 1) for child in self._children]
        )

    def add(self, pkg: "Package", indexes: list[int]) -> None:
        index = indexes.pop(0)
        if not indexes:
            self._children[index]._children.append(pkg)
        else:
            self._children[index].add(pkg, indexes)


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
            return f"{self._data}  {self._comment}"
        return super().__str__()


class With(Node):
    @classmethod
    def from_parsed(cls, data) -> "With":
        arg, body = data
        return cls(arg.children[0].value, body.children)

    def __str__(self) -> str:
        return f"with {self._data}:"


class If(Node):
    def __init__(
        self, data: str, children: list["Node"], elses: list[Union["Elif", "Else"]] = []
    ) -> None:
        super().__init__(data, children=children)
        self._elses = elses

    @classmethod
    def from_parsed(cls, data) -> "If":
        arg, body = data[0], data[1]
        return cls(arg.children[0].value, body.children, data[2:])

    def __str__(self) -> str:
        return f"if {self._data}:"

    def to_string(self, indent=0) -> str:
        return "\n".join(
            [super().to_string(indent=indent)]
            + [else_node.to_string(indent) for else_node in self._elses]
        )


class Elif(Node):
    @classmethod
    def from_parsed(cls, data) -> "Elif":
        arg, body = data
        return cls(arg.children[0].value, body.children)

    def __str__(self) -> str:
        return f"if {self._data}:"


class Else(Node):
    @classmethod
    def from_parsed(cls, data) -> "Else":
        return cls("else:", data[0].children)


class Root(Node):
    @classmethod
    def from_parsed(cls, data) -> "Root":
        return cls(None, data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}"

    def to_string(self, indent=0) -> str:
        return "\n".join(child.to_string(indent) for child in self._children)


class VurfTransformer(Transformer):
    def comment_stmt(self, data):
        return Comment.from_parsed(data)

    def package_stmt(self, data):
        return Package.from_parsed(data)

    def if_stmt(self, data):
        return If.from_parsed(data)

    def elif_stmt(self, data):
        return Elif.from_parsed(data)

    def else_stmt(self, data):
        return Else.from_parsed(data)

    def with_stmt(self, data):
        return With.from_parsed(data)

    def file_input(self, data):
        return Root.from_parsed(data)
