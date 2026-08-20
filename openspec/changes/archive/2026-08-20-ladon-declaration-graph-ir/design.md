## Design

### Goal

Create the smallest declaration graph kernel that can later consume
parser-helper reference candidates without coupling analysis to Lean extraction.

### Non-Goals

- Do not wire declaration graph data into reports yet.
- Do not claim semantic reference resolution beyond exact name matching.
- Do not add proof fragility or theorem-quality heuristics.
- Do not require Lake or external repositories for tests.

### IR

Add `LeanDeclaration`:

- `name`: fully qualified declaration name when known;
- `module`: owning module;
- `kind`: optional declaration kind;
- `references`: tuple of raw or resolved candidate declaration names.

The IR is intentionally conservative. Exact reference resolution is a future
step; this packet only builds graph edges when a reference exactly matches a
known declaration name.

### Analysis

Add `ladon.analysis.declaration_graph.summarize_declaration_graph`.

The summary should include:

- declaration count;
- resolved edge count;
- unresolved reference count;
- top fan-in declarations;
- top fan-out declarations;
- reachable and unreachable declarations from selected roots.

### Validation

Expected validation:

```bash
openspec validate ladon-declaration-graph-ir --strict
uv run pytest -q
uv run python scripts/python_quality.py --strict
uv run python -m compileall -q src tests scripts
uv build
```
