## MODIFIED Requirements

### Requirement: Ladon SHALL expose named pipeline phases

Ladon SHALL model a run as a sequence of named phases so analysis, reporting,
and future optimization work can target a specific boundary. The optional
`declaration_graph` phase SHALL be reported as `ok` when declaration IR is
available and `skipped` otherwise.

#### Scenario: Declaration graph phase is visible

- **WHEN** a run completes
- **THEN** `pipeline.timings.declaration_graph` is present
- **AND** it is `ok` if declaration IR was analyzed
- **AND** it is `skipped` if no declaration IR was available
