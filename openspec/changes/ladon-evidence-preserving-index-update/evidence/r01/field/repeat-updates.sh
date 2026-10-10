#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
for target in fixture adam; do
  for run in 1 2 3; do
    source_file="$ROOT/temp/index-history-field/$target/CapsuleFixture.lean"
    if [ "$target" = adam ]; then source_file="$ROOT/temp/index-history-field/adam/Mf/Optimization/FiniteMemoryAdam/CumulativePairing.lean"; fi
    printf '\n-- candidate update %s %s --\n' "$target" "$run" >> "$ROOT/temp/index-history-field/commands.log"
    printf '\n/- index-history-field repetition %s %s -/\n' "$target" "$run" >> "$source_file"
    printf 'source edit: append unique comment to %s\n' "$source_file" >> "$ROOT/temp/index-history-field/commands.log"
    (cd "$ROOT" && /usr/bin/time -v -o "temp/index-history-field/logs/${target}-repeat-${run}.time" uv run ladon proof-search index update --repo-root "$ROOT/temp/index-history-field/$target" --format json > "temp/index-history-field/logs/${target}-repeat-${run}.out" 2> "temp/index-history-field/logs/${target}-repeat-${run}.err")
    printf 'uv run ladon proof-search index update --repo-root %s --format json\n' "$ROOT/temp/index-history-field/$target" >> "$ROOT/temp/index-history-field/commands.log"
  done
done
