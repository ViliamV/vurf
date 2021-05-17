from lark import Lark
from lark.indenter import Indenter
from pathlib import Path
from vurf.transformer import VurfTransformer


class PythonesqueIndenter(Indenter):
    NL_type = "_NEWLINE"
    OPEN_PAREN_types = []
    CLOSE_PAREN_types = []
    INDENT_type = "_INDENT"
    DEDENT_type = "_DEDENT"
    tab_len = 2


kwargs = dict(rel_to=__file__, postlex=PythonesqueIndenter(), start="file_input", parser='lalr', transformer=VurfTransformer())

parser = Lark.open("grammar.lark", **kwargs)

with open(Path(__file__).parent / "test.vurf") as f:
    root = parser.parse(f.read() + "\n")

print(root.to_string())

#  print(transformed)
