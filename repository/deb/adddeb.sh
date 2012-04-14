#!/bin/bash

repo=$(dirname "$0")
file="$1"

if ! [ -e "$file" ]; then
  echo "Usage: $0 package.deb"
  exit 1
fi

if ! which reprepro >/dev/null; then
  echo "Reprepro not installed"
  exit 2
fi

for distro in stable lenny squeeze; do
  reprepro -b "$repo" includedeb "$distro" "$file"
done
