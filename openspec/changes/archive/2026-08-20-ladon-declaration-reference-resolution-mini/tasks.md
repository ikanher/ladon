# Tasks

- [x] Add tests for module-local reference resolution.
- [x] Add tests for unique basename resolution.
- [x] Add tests for ambiguous basename remaining unresolved.
- [x] Add conservative resolver to declaration graph analysis.
- [x] Validate with `openspec validate ladon-declaration-reference-resolution-mini --strict`.
- [x] Validate with `uv run pytest -q`.
- [x] Validate with `uv run python scripts/python_quality.py --strict`.
- [x] Validate with `uv run python -m compileall -q src tests scripts`.
- [x] Validate with `uv build`.
- [x] Smoke-run Lean root backend against Quux and compare unresolved counts.
