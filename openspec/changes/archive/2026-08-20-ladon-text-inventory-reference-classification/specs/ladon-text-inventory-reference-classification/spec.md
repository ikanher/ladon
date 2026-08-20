## ADDED Requirements

### Requirement: Known Inventory Reference Classification

Ladon SHALL use text-discovered declaration names to classify unresolved
reference candidates that are known elsewhere in the repository inventory.

#### Scenario: graph analysis classifies known inventory candidates

- GIVEN declaration graph analysis receives a known-reference inventory
- AND an unresolved candidate matches that inventory
- WHEN unresolved rows are emitted
- THEN the row SHALL be classified as `known_inventory_candidate`.

#### Scenario: known inventory candidates are not actionable unresolved rows

- GIVEN an unresolved candidate is classified as `known_inventory_candidate`
- WHEN actionable unresolved rows are emitted
- THEN that candidate SHALL be excluded.

#### Scenario: pipeline passes text declaration inventory

- GIVEN text discovery sees a declaration in a sibling module
- AND Lean root extraction references the declaration by basename
- WHEN the pipeline runs
- THEN the declaration graph SHALL classify the candidate as
  `known_inventory_candidate`.
