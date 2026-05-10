## ADDED Requirements

### Requirement: Ladon SHALL provide a strict Python quality gate

Ladon SHALL expose a project-local strict quality command that combines radon,
vulture, compile checks, and tests into an actionable gate.

#### Scenario: Strict quality command passes on clean active code

- **WHEN** `uv run python scripts/python_quality.py --strict` is run from the
  Ladon project root
- **THEN** it exits successfully only if active Python targets satisfy the
  configured radon and vulture thresholds
- **AND** it prints the commands or checks used

#### Scenario: Strict quality command rejects high-complexity code

- **WHEN** a checked active Python target contains a C-or-worse radon
  cyclomatic complexity block
- **THEN** strict mode exits nonzero
- **AND** it reports the offending file, object name, rank, and complexity

### Requirement: Ladon SHALL keep high-confidence dead-code findings out of active code

Ladon SHALL treat vulture high-confidence findings as strict-gate failures for
active source, tests, and scripts.

#### Scenario: Vulture reports no high-confidence findings

- **WHEN** strict quality mode runs vulture with minimum confidence `80`
- **THEN** no high-confidence finding is allowed in active targets
- **AND** any required false-positive suppression is explicit and reviewed in
  source control

### Requirement: Ladon's package entrypoint SHALL NOT import the legacy monolith

The active `ladon` package entrypoint SHALL route through clean core modules
instead of importing the old all-in-one analyzer module.

#### Scenario: Importing ladon uses clean entrypoint

- **WHEN** Python imports `ladon.main`
- **THEN** the import does not import `ladon.ladon`
- **AND** CLI behavior is provided by a small clean module such as `ladon.cli`

### Requirement: Ladon's clean core SHALL preserve tested module-DAG reporting

The clean core SHALL preserve a tested smoke path for Lean module discovery,
module-DAG analysis, and JSON/text report rendering.

#### Scenario: Tiny Lean fixture report is generated

- **WHEN** the CLI analyzes a local tiny Lean fixture with `--skip-build`
- **THEN** JSON output contains metadata and a module-DAG summary
- **AND** text output contains a concise module-DAG section
- **AND** no Lake invocation is required for this smoke path

### Requirement: Ladon SHALL make unsupported legacy-only features explicit

Clean-core Ladon SHALL fail or warn explicitly for advanced legacy-only options
that have not yet been rebuilt with tests.

#### Scenario: Unsupported advanced option is requested

- **WHEN** a user requests a legacy-only advanced feature not implemented in the
  clean core
- **THEN** Ladon exits nonzero or emits a clear unsupported-feature warning
- **AND** it does not emit a report that pretends the feature was audited
  successfully

### Requirement: Ladon SHALL avoid new monoliths

New clean-core functionality SHALL be split into small modules with explicit
responsibilities and pure analysis seams.

#### Scenario: Quality gate covers active modules

- **WHEN** strict quality mode scans active source targets
- **THEN** no active source file may remain C-grade by maintainability index
- **AND** no active function or method may remain C-or-worse by radon
  cyclomatic complexity
