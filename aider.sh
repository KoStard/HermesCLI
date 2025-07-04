#!/bin/bash

# Editable file
editable_file="./docs/tasks.md"

# Files to mark as read-only (philosophy.md and all __init__.py files)
read_only_files=("./docs/philosophy.md")
while IFS= read -r file; do
  read_only_files+=("$file")
done < <(find hermes -type f -name "__init__.py")

# Build the command using an array (safer than string concatenation + eval)
args=()
args+=(aider)
for file in "${read_only_files[@]}"; do
  args+=(--read "$file")
done
args+=(--file "$editable_file")

# Execute the command with all arguments preserved
"${args[@]}" "$@"
