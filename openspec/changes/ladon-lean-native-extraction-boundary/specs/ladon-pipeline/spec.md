## MODIFIED Requirements

### Requirement: Ladon SHALL expose named pipeline phases

Ladon SHALL model a run as a sequence of named phases so analysis, reporting,
and future optimization work can target a specific boundary. The
`lean_extraction` phase SHALL be skipped for the text backend and executed for
the Lean backend.

#### Scenario: Required phases are visible

- **WHEN** Ladon completes a normal repository audit
- **THEN** the run result includes entries for `discover`, `lean_extraction`,
  `indexing`, `module_dag`, `findings`, and `rendering`
- **AND** `lean_extraction` reports `skipped` for text extraction
- **AND** `lean_extraction` reports `ok` for successful Lean-native extraction
