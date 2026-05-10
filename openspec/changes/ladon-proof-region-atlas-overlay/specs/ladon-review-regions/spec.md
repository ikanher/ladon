## ADDED Requirements

### Requirement: Review Region Overlay

Ladon SHALL group related report signals into additive review regions.

#### Scenario: import pressure region

- GIVEN root import closure or composite import-pressure findings
- WHEN review regions are summarized
- THEN an import-pressure region SHALL be present.

#### Scenario: proof-family region

- GIVEN declaration-family rows or proof-family similarity candidates
- WHEN review regions are summarized
- THEN a proof-family region SHALL be present.

#### Scenario: packet evidence region

- GIVEN packet evidence rows
- WHEN review regions are summarized
- THEN a packet-evidence region SHALL be present.
