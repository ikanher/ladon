# Tasks

- [x] Add tests for parser-helper JSON normalization into `LeanModule`.
- [x] Add tests that text backend leaves `lean_extraction` skipped.
- [x] Add tests that a fake Lean backend runner records `lean_extraction=ok`
  and extraction counters.
- [x] Add `--extraction-backend {text,lean}` CLI option.
- [x] Add root-only default for Lean extraction and explicit inventory opt-in.
- [x] Add parser-helper JSON normalization functions.
- [x] Add Lean backend runner seam that can be faked in tests.
- [x] Wire backend selection through `RunContext` and `run_pipeline`.
- [x] Keep module-DAG analysis backend-agnostic.
- [x] Validate with `openspec validate ladon-lean-native-extraction-boundary --strict`.
- [x] Validate with `uv run pytest -q`.
- [x] Validate with `uv run python scripts/python_quality.py --strict`.
- [x] Validate with `uv run python -m compileall -q src tests scripts`.
- [x] Validate with `uv build`.
- [x] Smoke-run text backend against Quux under `/tmp`.
- [x] Attempt a Lean backend smoke run against Quux if local Lake dependencies
  are available; record if unavailable.
