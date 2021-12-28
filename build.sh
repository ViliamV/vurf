#!/usr/bin/env bash

set -e
set -u
set -x

DIR=$(dirname "$0")
INPUT_FILE="$DIR/vurf/parser/grammar.lark"
OUTPUT_FILE="$DIR/vurf/parser/stand_alone.py"


rm "$OUTPUT_FILE"
poetry run python -m lark.tools.standalone "$INPUT_FILE" > "$OUTPUT_FILE"
