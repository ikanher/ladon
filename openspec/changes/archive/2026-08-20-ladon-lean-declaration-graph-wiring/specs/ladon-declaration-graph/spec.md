## MODIFIED Requirements

### Requirement: Ladon SHALL summarize exact declaration-reference graphs

Ladon SHALL provide a pure analysis pass that builds declaration edges only for
references that exactly match known declaration names. When the pipeline has
declaration IR, it SHALL expose the summary additively in reports.

#### Scenario: Known references become report edges

- **WHEN** Lean extraction provides declaration IR and exact references
- **THEN** the JSON report includes `declaration_graph`
- **AND** the text report includes a declaration graph summary section
