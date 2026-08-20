# Tasks

- [x] Add pipeline test for Lean root backend preserving text module inventory.
- [x] Add test for helper row overriding text module row.
- [x] Implement module inventory merge helper.
- [x] Wire Lean backend to analyze merged modules.
- [x] Validate with `openspec validate ladon-lean-backend-preserve-module-inventory --strict`.
- [x] Validate with `uv run pytest -q`.
- [x] Validate with `uv run python scripts/python_quality.py --strict`.
- [x] Validate with `uv run python -m compileall -q src tests scripts`.
- [x] Validate with `uv build`.
- [x] Smoke-run Lean root backend against Quux and matrix-factorization.
