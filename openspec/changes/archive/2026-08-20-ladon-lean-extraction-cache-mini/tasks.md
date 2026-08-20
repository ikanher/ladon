# Tasks

- [x] Add tests for cache hit/miss helper behavior.
- [x] Add tests for source-content cache invalidation.
- [x] Add CLI option for an optional Lean extraction cache directory.
- [x] Implement content-addressed helper payload cache.
- [x] Surface cache counters in pipeline timing.
- [x] Validate with `openspec validate ladon-lean-extraction-cache-mini --strict`.
- [x] Validate with `uv run pytest -q`.
- [x] Validate with `uv run python scripts/python_quality.py --strict`.
- [x] Validate with `uv run python -m compileall -q src tests scripts`.
- [x] Validate with `uv build`.
- [x] Smoke-run two cached Lean root passes against Quux under `/tmp`.
