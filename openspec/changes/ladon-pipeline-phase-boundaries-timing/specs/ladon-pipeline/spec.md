## ADDED Requirements

### Requirement: Ladon SHALL expose named pipeline phases

Ladon SHALL model a run as a sequence of named phases so analysis, reporting,
and future optimization work can target a specific boundary.

#### Scenario: Required phases are visible

- **WHEN** Ladon completes a normal repository audit
- **THEN** the run result includes entries for `discover`, `lean_extraction`,
  `indexing`, `module_dag`, `findings`, and `rendering`
- **AND** optional phases such as `declaration_graph`, `witness_audit`, and
  `openspec_audit` are either present with an explicit skipped status or absent
  by documented policy

### Requirement: Ladon SHALL record stable phase timing metadata

Ladon SHALL emit deterministic timing keys for each executed phase while
allowing elapsed values to vary across machines.

#### Scenario: Timing metadata has stable shape

- **WHEN** a phase is executed
- **THEN** its timing record includes the phase name, elapsed seconds, and a
  status
- **AND** elapsed seconds are nonnegative
- **AND** tests assert key presence and invariants rather than exact duration

### Requirement: Ladon SHALL separate pure analysis kernels from side effects

Ladon SHALL keep graph and proof-structure analysis in pure modules that accept
normalized IR and return plain data.

#### Scenario: Module DAG analysis is reusable

- **WHEN** legacy module extraction produces module/import information
- **THEN** that data can be adapted into the shared `LeanModule` IR
- **AND** the CLI path and unit tests use the same module DAG analyzer
- **AND** the analyzer does not invoke Lean, inspect the filesystem, or render
  reports

### Requirement: Ladon SHALL preserve report compatibility during pipeline refactors

Pipeline fields SHALL be additive until a deliberate breaking-change packet is
opened.

#### Scenario: Existing JSON consumers keep working

- **WHEN** pipeline timing metadata is added to JSON output
- **THEN** existing top-level keys remain available
- **AND** timing metadata is placed under a namespaced key such as
  `pipeline.timings` or `metadata.pipeline_timings`
- **AND** the text report keeps its existing root-focused sections unless a
  later packet explicitly changes them

### Requirement: Ladon SHALL include a small fixture for pipeline tests

Ladon SHALL carry a minimal local fixture or pure synthetic fixture sufficient
to test pipeline shape without depending on a large external Lean repository.

#### Scenario: Pipeline smoke tests are local

- **WHEN** the test suite validates phase boundaries
- **THEN** it can run against a small fixture or synthetic extraction data
- **AND** it does not require `/home/codex/projects/quux` or
  `/home/codex/projects/lean/matrix-factorization`
