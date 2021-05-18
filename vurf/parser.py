from io import TextIOWrapper
from typing import cast
from lark import Lark
from lark.indenter import Indenter
from vurf.transformer import VurfTransformer, Root

class PythonesqueIndenter(Indenter):
    NL_type = "_NEWLINE"
    OPEN_PAREN_types = []
    CLOSE_PAREN_types = []
    INDENT_type = "_INDENT"
    DEDENT_type = "_DEDENT"
    tab_len = 2


def parse(file: TextIOWrapper) -> Root:
    parser = Lark.open(
        "grammar.lark",
        rel_to=__file__,
        postlex=PythonesqueIndenter(),
        start="file_input",
        parser="lalr",
        transformer=VurfTransformer(),
    )
    # Add extra newline in case there is none
    return cast(Root, parser.parse(file.read() + '\n'))
