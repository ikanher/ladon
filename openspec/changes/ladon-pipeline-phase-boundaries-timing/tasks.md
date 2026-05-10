# Tasks

- [x] Add `RunContext`, `PipelineResult`, and `PhaseTiming` dataclasses with a
  small timing helper.
- [x] Add tests that required phase timing keys exist and have nonnegative
  elapsed values without snapshotting exact durations.
- [x] Add a legacy adapter test that converts current extraction/module data
  into `LeanModule`.
- [x] Route the CLI module dependency summary through
  `ladon.analysis.module_dag` instead of keeping duplicate DAG logic.
- [x] Add a minimal local fixture or synthetic extraction fixture for pipeline
  smoke tests.
- [x] Add JSON report timing metadata under a compatibility-safe namespace.
- [x] Add text report summary for slowest phases without moving actionable
  root-focused findings below repo-wide inventory.
- [x] Keep `uv run python scripts/python_quality.py` clean for vulture and use
  radon output to prioritize phase-extraction work.
- [x] Validate with `uv run pytest -q`.
- [x] Validate with `uv run python scripts/python_quality.py`.
- [x] Validate with `uv run python -m compileall -q src tests`.
- [x] Validate with `uv build`.
- [x] Run a smoke audit against Quux or matrix-factorization and save output
  under `/tmp` rather than committing generated reports.
