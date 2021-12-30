#!/usr/bin/env bash

# Make any argument mean DRY_RUN
DRY_RUN=$1

export VURF_SECTION=linux

# explicitly installed packages not in the base meta package or base-devel package group
for package in $(comm -23 <(comm -23 <(pacman -Qqe | sort) <({ pacman -Qqg base-devel; expac -l '\n' '%E' base; } | sort -u) | sort) <(vurf packages | sort)); do
  if [[ -n $DRY_RUN ]]; then
    echo "$package not in vurf"
  else
    vurf add "$(expac -H M "%n  # %d" $package)"
    echo "Adding $package to packages.vurf"
  fi
done

for package in $(comm -13 <(comm -23 <(pacman -Qqe | sort) <({ pacman -Qqg base-devel; expac -l '\n' '%E' base; } | sort -u) | sort) <(vurf packages | sort)); do
  if [[ -n $DRY_RUN ]]; then
    echo "$package not installed"
  else
    vurf remove "$package"
    echo "Removing $package from packages.vurf"
  fi
done
