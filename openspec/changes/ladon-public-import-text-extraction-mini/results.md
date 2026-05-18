# Results

## Mathlib Smoke

Command:

```bash
uv run ladon \
  --repo-root /home/codex/projects/quux/.lake/packages/mathlib \
  --root Mathlib \
  --skip-build \
  --output-json temp/mathlib-ladon-smoke/report.json \
  --output-text temp/mathlib-ladon-smoke/report.txt
```

Observed after applying the text-import parser fix:

```text
module_count: 7649
edge_count: 31648
acyclic: true
cyclic_component_count: 0
source_modules_not_reachable_from_chosen_roots_count: 1
```

This replaces the failed smoke evidence from the proposal: roughly `270` edges
and false cycles from documentation import examples.
