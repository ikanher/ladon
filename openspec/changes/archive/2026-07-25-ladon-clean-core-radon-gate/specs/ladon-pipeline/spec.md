## MODIFIED Requirements

### Requirement: Ladon SHALL separate pure analysis kernels from side effects

Ladon SHALL keep graph and proof-structure analysis in pure modules that accept
normalized IR and return plain data. The clean-core refactor SHALL preserve this
boundary and SHALL NOT replace the old monolith with a new monolith.

#### Scenario: Module DAG analysis is reusable

- **WHEN** the clean CLI obtains module/import information from text extraction
  or future Lean-native extraction
- **THEN** that data can be adapted into the shared `LeanModule` IR
- **AND** the CLI path and unit tests use the same module DAG analyzer
- **AND** the analyzer does not invoke Lean, inspect the filesystem, or render
  reports
