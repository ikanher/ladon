## ADDED Requirements

### Requirement: Atlas SQLite Query Surface

Ladon SHALL provide a deterministic SQLite artifact derived from atlas JSON.

#### Scenario: SQLite export preserves atlas rows

- GIVEN an atlas JSON graph exists
- WHEN SQLite export runs
- THEN the database SHALL contain normalized node, edge, report, finding,
  review-region, signal, declaration-highlight, and module-highlight tables.

#### Scenario: canned queries answer reviewer questions

- GIVEN an atlas SQLite database exists
- WHEN a canned query runs
- THEN Ladon SHALL return deterministic rows for hotspot, recurring
  declaration, review-region pressure, or proof-family pressure questions.
