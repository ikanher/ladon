## MODIFIED Requirements

### Requirement: Ladon SHALL summarize exact declaration-reference graphs

Ladon SHALL provide a pure analysis pass that builds declaration edges only when
reference candidates resolve conservatively to known declaration names. Reports
SHALL expose actionable triage rows for fan-in, fan-out, and unresolved
reference candidates.

#### Scenario: Unresolved reference candidates are summarized

- **WHEN** unresolved reference candidates remain
- **THEN** the declaration graph summary includes top unresolved candidate
  counts
- **AND** each row includes a small sample of source declarations

#### Scenario: Text report includes declaration graph triage

- **WHEN** declaration graph data is available
- **THEN** the text report includes top fan-in, top fan-out, and unresolved
  reference rows
