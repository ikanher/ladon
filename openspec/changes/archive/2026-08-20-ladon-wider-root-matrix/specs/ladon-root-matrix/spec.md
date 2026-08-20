## ADDED Requirements

### Requirement: Maintained Local Root Matrix

Ladon SHALL provide a maintained local root matrix for manual calibration runs.

#### Scenario: dry-run command generation

- GIVEN the root-matrix script is run in dry-run mode
- WHEN commands are printed
- THEN each command SHALL include a repo root, analysis root, and JSON/text
  output path.

#### Scenario: named entry selection

- GIVEN an entry name filter is provided
- WHEN the matrix is selected
- THEN only matching entries SHALL be returned.

#### Scenario: no sibling-repo CI dependency

- GIVEN unit tests run
- WHEN root-matrix behavior is tested
- THEN tests SHALL validate command generation without requiring Quux or
  matrix-factorization to exist.
