# Tasks

- [x] Add CLI smoke tests for a tiny local Lean fixture: JSON output, text
  output, and no Lake requirement under `--skip-build`.
- [x] Add import-boundary test proving `import ladon` does not import
  `ladon.ladon`.
- [x] Add strict quality-gate tests for synthetic radon C-or-worse failure and
  vulture high-confidence failure.
- [x] Extend `scripts/python_quality.py` with `--strict` and machine-parsed
  radon/vulture checks.
- [x] Add or refactor a small clean CLI module that owns argument parsing and
  orchestration.
- [x] Add clean text-based Lean module discovery for smoke/module-DAG runs.
- [x] Add clean JSON/text renderers for the tested module-DAG report.
- [x] Rewire `src/ladon/__init__.py` and package script entrypoint to the clean
  CLI module.
- [x] Delete the legacy `src/ladon/ladon.py` monolith, or quarantine it outside
  active quality targets with an explicit removal note if deletion is unsafe.
- [x] Refactor any remaining active radon C-or-worse functions, including
  existing module-DAG helpers if they fail strict mode.
- [x] Update README with the strict quality workflow and current supported CLI
  surface.
- [x] Update the global Ladon skill if CLI flags or support boundaries changed.
- [x] Validate with `uv run pytest -q`.
- [x] Validate with `uv run python scripts/python_quality.py --strict`.
- [x] Validate with `uv run python -m compileall -q src tests scripts`.
- [x] Validate with `uv build`.
- [x] Smoke-run `bin/ladon` against Quux with outputs under `/tmp`.
