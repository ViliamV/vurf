import sys

from io import TextIOWrapper
from typing import cast

from vurf.nodes import Root
from vurf.parser.indenter import PythonesqueIndenter
from vurf.parser.stand_alone import Lark_StandAlone, ParseError
from vurf.parser.transformer import Root, VurfTransformer


def parse(file: TextIOWrapper) -> Root:
    parser = Lark_StandAlone(
        postlex=PythonesqueIndenter(),
        transformer=VurfTransformer(),
    )
    try:
        # Add extra newline in case there is none
        return cast(Root, parser.parse(file.read() + "\n"))
    except ParseError as e:
        sys.stderr.write(" ".join(map(str, e.args)) + "\n")
        sys.exit(1)
