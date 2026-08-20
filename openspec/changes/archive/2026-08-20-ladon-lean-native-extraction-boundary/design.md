## Design

### Goal

Introduce a clean, test-backed Lean-native extraction seam without restoring
legacy declaration/proof heuristics.

### Non-Goals

- Do not implement declaration graph analysis in this packet.
- Do not inspect proof bodies beyond preserving parser-helper output fields that
  future packets can use.
- Do not make Lean extraction the default yet.
- Do not require Quux or matrix-factorization for unit tests.

### Backend Model

Supported backend values:

- `text`: current regex-based module/import/declaration discovery. This remains
  default and requires no Lake invocation.
- `lean`: runs the bundled `ladon_parser_helper.lean` through the target repo's
  `lake env lean --run` and normalizes its JSON output into `LeanModule`.

The first Lean backend implementation extracts the selected analysis root by
default. Full-inventory extraction is explicit opt-in because spawning one Lake
process per file is too slow for large repositories without caching/batching.

### Data Boundary

Add helper-facing types/functions only as needed:

- parse `header.imports[*].module` into `LeanModule.imports`;
- parse declaration-like commands with `declarationFullName` or
  `declarationName` into `LeanModule.declarations`;
- keep the current stable `LeanModule` map as the analysis input.

### Pipeline Semantics

- `text` backend: `discover` resolves root/inventory, `lean_extraction` is
  skipped, `indexing` parses source text.
- `lean` backend: `discover` resolves root/inventory, `lean_extraction` runs
  the parser helper and records module/declaration counters, `indexing` adapts
  helper modules to `LeanModule`.

### Validation

Expected validation:

```bash
openspec validate ladon-lean-native-extraction-boundary --strict
uv run pytest -q
uv run python scripts/python_quality.py --strict
uv run python -m compileall -q src tests scripts
uv build
bin/ladon --repo-root /home/codex/projects/quux --root Quux/Semantics/Propagation.lean --skip-build --extraction-backend text --output-json /tmp/ladon-text.json --output-text /tmp/ladon-text.txt
```

If local Lake/Lean is available for Quux, also run:

```bash
bin/ladon --repo-root /home/codex/projects/quux --root Quux/Semantics/Propagation.lean --extraction-backend lean --output-json /tmp/ladon-lean.json --output-text /tmp/ladon-lean.txt
```
