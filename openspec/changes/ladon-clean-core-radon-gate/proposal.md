## Why

Ladon should not start its standalone life by carrying a 6000-line legacy
monolith with F-grade radon findings. The shared project needs a small,
test-backed core where code-quality tools are hard signals, not decorative
reports.

## What Changes

- Add a strict Python quality gate backed by `radon`, `vulture`, compile checks,
  and tests.
- Replace the package entrypoint path so it does not import the legacy monolith.
- Build the clean core in TDD order: CLI/report behavior tests first, then
  refactor or remove high-complexity code.
- Keep useful functionality at the current seed level: module discovery,
  module-DAG summary, JSON/text output, and explicit warnings for unsupported
  legacy-only advanced options.
- Define an explicit temporary quarantine policy only if deletion is unsafe:
  quarantined legacy code must not be imported by `ladon`, must not be shipped
  as the active CLI, and must not be included in strict quality targets.

## Capabilities

### New Capabilities

- `ladon-python-quality`: Defines Ladon's strict Python quality gate,
  no-legacy-core policy, quality-command behavior, and acceptance thresholds.

### Modified Capabilities

- `ladon-pipeline`: The clean core must remain compatible with the pipeline
  direction by keeping phase-friendly seams and avoiding another monolith.

## Impact

- Affected code: `src/ladon/`, `scripts/python_quality.py`, tests, and package
  entrypoint wiring.
- Affected workflow: `uv run python scripts/python_quality.py --strict` becomes
  a required validation command.
- Affected downstream users: current CLI flags for core module-DAG runs remain
  supported; advanced legacy-only flags may become explicit unsupported
  warnings until reintroduced through clean modules.
