## MODIFIED Requirements

### Requirement: Ladon SHALL summarize exact declaration-reference graphs

Ladon SHALL provide a pure analysis pass that builds declaration edges only when
reference candidates resolve conservatively to known declaration names. It SHALL
resolve exact matches, module-local names, and unique basenames; it SHALL NOT
resolve ambiguous or unknown candidates.

#### Scenario: Module-local reference resolves

- **WHEN** declaration `A.root` references candidate `helper`
- **AND** known declaration `A.helper` exists
- **THEN** the graph contains an edge from `A.root` to `A.helper`

#### Scenario: Unique basename resolves

- **WHEN** declaration `A.root` references candidate `shared`
- **AND** exactly one known declaration has basename `shared`
- **THEN** the graph contains an edge to that known declaration

#### Scenario: Ambiguous basename remains unresolved

- **WHEN** declaration `A.root` references candidate `shared`
- **AND** more than one known declaration has basename `shared`
- **THEN** no graph edge is fabricated
- **AND** the candidate contributes to unresolved reference count
