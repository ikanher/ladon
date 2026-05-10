## ADDED Requirements

### Requirement: Unresolved Reference Class Summary

Ladon SHALL summarize unresolved reference counts by classification.

#### Scenario: JSON class counts are emitted

- GIVEN unresolved references have classifications
- WHEN declaration graph analysis runs
- THEN the summary SHALL include `unresolved_reference_classes` sorted by
  descending count.

#### Scenario: text report renders class counts

- GIVEN declaration graph summary includes unresolved class counts
- WHEN text rendering runs
- THEN the report SHALL include an `Unresolved Reference Classes` section.
