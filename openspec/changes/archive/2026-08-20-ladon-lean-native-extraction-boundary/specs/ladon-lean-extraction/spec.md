## ADDED Requirements

### Requirement: Ladon SHALL support explicit extraction backend selection

Ladon SHALL let users choose between text extraction and Lean-native extraction
without changing the default clean-core behavior.

#### Scenario: Text backend remains default

- **WHEN** the CLI is run without `--extraction-backend`
- **THEN** Ladon uses the text backend
- **AND** `lean_extraction` remains an explicitly skipped pipeline phase

#### Scenario: Lean backend is requested

- **WHEN** the CLI is run with `--extraction-backend lean`
- **THEN** Ladon attempts to run the bundled parser helper through the target
  repository's Lake environment
- **AND** parser-helper output is normalized into the same `LeanModule` IR used
  by the text backend

### Requirement: Ladon SHALL normalize parser-helper JSON into stable module IR

Ladon SHALL convert parser-helper imports and declaration-like commands into
`LeanModule` without exposing parser-helper internals to pure analysis passes.

#### Scenario: Parser output contains imports and declarations

- **WHEN** parser-helper JSON contains header imports and declaration-like
  commands
- **THEN** normalized `LeanModule.imports` preserves imported module names
- **AND** normalized `LeanModule.declarations` contains declaration full names
  when available

### Requirement: Ladon SHALL time Lean extraction as its own phase

The pipeline SHALL record `lean_extraction` as `ok` only when the Lean backend
actually runs parser-helper extraction.

#### Scenario: Lean extraction phase records counters

- **WHEN** the Lean backend completes
- **THEN** `pipeline.timings.lean_extraction.status` is `ok`
- **AND** the timing counters include extracted module and declaration counts

### Requirement: Ladon SHALL keep analysis passes backend-agnostic

Pure analysis passes SHALL consume `LeanModule` maps regardless of extraction
backend.

#### Scenario: Module DAG receives normalized modules

- **WHEN** either backend completes extraction/indexing
- **THEN** `ladon.analysis.module_dag` receives a mapping of module names to
  `LeanModule`
- **AND** it does not know whether modules came from text or Lean extraction
