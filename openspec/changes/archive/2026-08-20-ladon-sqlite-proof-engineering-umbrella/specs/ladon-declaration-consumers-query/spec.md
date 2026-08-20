## ADDED Requirements

### Requirement: Direct semantic dependencies are complete when claimed
Semantic extraction SHALL store every Lean-supplied direct type and value dependency through the symbol dictionary with source, target, ownership, authority, and module coverage.

#### Scenario: External target is used
- **WHEN** a project declaration references a dependency declaration absent from local declaration rows
- **THEN** the edge targets an external symbol row and remains queryable as frontier evidence

### Requirement: Consumers use an indexed reverse lookup
`proof-search consumers` SHALL resolve one exact declaration symbol and return bounded source declarations through the reverse dependency index, separated by type/value kind and filtered by ownership.

#### Scenario: Primitive has type and proof-body users
- **WHEN** both kinds of direct consumers exist
- **THEN** the response reports each consumer once with its dependency kind, source location, ownership, and scope reason

### Requirement: Empty consumers require complete coverage
The system MUST report a confirmed empty consumer set only when all selected module dependency populations are complete and current.

#### Scenario: One module is partial
- **WHEN** no stored consumer rows match but a selected module has partial dependency extraction
- **THEN** the response is partial with omission evidence and does not claim absence

### Requirement: Consumer queries remain set-oriented
The number of SQL statements used for one request SHALL remain constant as returned consumer count grows within the output cap.

#### Scenario: Fixture doubles consumers
- **WHEN** a trace fixture increases the number of matching rows
- **THEN** statement-count assertions remain unchanged
