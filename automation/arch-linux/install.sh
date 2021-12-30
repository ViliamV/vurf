#!/usr/bin/env bash

files=("/etc/pacman.d/hooks/vurf.hook" "/etc/pacman.d/hooks.bin/vurf-compare.sh")
for file in "${files[@]}"; do
    if [[ ! -f $file ]]; then
        sudo mkdir -p "$(dirname "$file")"
        sudo cp "$(basename $file)" "$file"
    fi
done

