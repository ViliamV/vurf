from lark import Transformer

from vurf.nodes import *


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
