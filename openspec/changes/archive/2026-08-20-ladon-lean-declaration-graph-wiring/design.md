## Design

### Goal

Wire declaration reference data from Lean-native extraction into the existing
pure declaration graph analyzer.

### Non-Goals

- Do not add heuristic namespace resolution.
- Do not add proof-fragility findings.
- Do not make declaration graph reports appear for text extraction unless a
  later packet defines text declaration semantics.

### Extraction Bundle

Add an `ExtractionBundle` style object with:

- `modules: dict[str, LeanModule]`
- `declarations: dict[str, LeanDeclaration]`

The Lean backend returns this bundle. The text backend can be adapted into a
bundle with modules and an empty declaration map.

### Pipeline

Add a `declaration_graph` phase:

- `ok` when declarations exist;
- `skipped` when no declaration IR is present.

The resulting summary is additive under `declaration_graph` in JSON and a small
text section.

### Validation

```bash
openspec validate ladon-lean-declaration-graph-wiring --strict
uv run pytest -q
uv run python scripts/python_quality.py --strict
uv run python -m compileall -q src tests scripts
uv build
bin/ladon --repo-root /home/codex/projects/quux --root Quux/Semantics/Propagation.lean --extraction-backend lean --lean-extraction-scope root --output-json /tmp/ladon-lean-decl.json --output-text /tmp/ladon-lean-decl.txt
```
