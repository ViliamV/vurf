#!/usr/bin/env bash

DIR=$(dirname "$0")/vurf_completions

for sh in bash zsh fish; do
  file="$DIR/completions.$sh"
  rm -f "file"
  _VURF_COMPLETE="${sh}_source" poetry run vurf > "$file"
done
