from vurf.parser.stand_alone import Indenter


class PythonesqueIndenter(Indenter):
    NL_type = "_NEWLINE"
    OPEN_PAREN_types: list[str] = []
    CLOSE_PAREN_types: list[str] = []
    INDENT_type = "_INDENT"
    DEDENT_type = "_DEDENT"
    tab_len = 2
