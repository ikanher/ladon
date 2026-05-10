# Tasks

- [x] Add extraction bundle IR for modules plus declarations.
- [x] Normalize parser-helper reference candidates into `LeanDeclaration`.
- [x] Add tests for helper payload declaration normalization.
- [x] Add pipeline tests for `declaration_graph=ok` with fake Lean bundle.
- [x] Add pipeline tests for `declaration_graph=skipped` with text backend.
- [x] Add JSON/text declaration graph report output.
- [x] Validate with `openspec validate ladon-lean-declaration-graph-wiring --strict`.
- [x] Validate with `uv run pytest -q`.
- [x] Validate with `uv run python scripts/python_quality.py --strict`.
- [x] Validate with `uv run python -m compileall -q src tests scripts`.
- [x] Validate with `uv build`.
- [x] Smoke-run Lean root backend against Quux under `/tmp`.
