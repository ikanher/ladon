# Tasks

- [x] Add focused extraction tests for `public import`, `public meta import`,
  `import all`, and trailing import comments.
- [x] Add focused extraction tests proving imports inside block comments or
  module docstrings are ignored.
- [x] Update the text import parser in `src/ladon/extraction.py`.
- [x] Add a module-DAG regression proving docstring self-import examples do not
  create cyclic components.
- [x] Re-run a fast mathlib smoke report under `temp/mathlib-ladon-smoke/` and
  record the improved edge count and cycle status.
- [x] Validate with `openspec validate ladon-public-import-text-extraction-mini --strict`.
- [x] Validate with `uv run pytest -q`.
- [x] Validate with `uv run python scripts/python_quality.py --strict`.
- [x] Validate with `uv run python -m compileall -q src tests scripts`.
- [x] Validate with `uv build`.
