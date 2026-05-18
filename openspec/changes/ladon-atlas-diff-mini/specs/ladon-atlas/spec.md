## ADDED Requirements

### Requirement: Atlas Diff

Ladon SHALL provide a deterministic diff over two atlas JSON artifacts.

#### Scenario: added and removed rows

- GIVEN two atlas JSON artifacts
- WHEN a finding, region, signal, declaration highlight, or module highlight is
  present in only one artifact
- THEN the diff SHALL report the row as added or removed by category.

#### Scenario: changed rows

- GIVEN two atlas JSON artifacts contain the same normalized row key
- AND the row payload differs
- WHEN atlas diff runs
- THEN the diff SHALL report the row as changed with before and after payloads.
