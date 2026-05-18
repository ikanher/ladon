## ADDED Requirements

### Requirement: Report Atlas Export

Ladon SHALL export a deterministic atlas from generated report JSON files.

#### Scenario: atlas includes report nodes

- GIVEN a directory containing Ladon report JSON files
- WHEN atlas export runs
- THEN the atlas SHALL include one report node per report.

#### Scenario: atlas includes review-surface graph links

- GIVEN reports include roots, findings, review regions, modules, and
  declarations
- WHEN atlas export runs
- THEN the atlas SHALL include nodes and edges linking reports to those
  review-surface signals.

#### Scenario: markdown summary is generated

- GIVEN an atlas graph
- WHEN markdown rendering runs
- THEN it SHALL include summary counts and top report rows suitable for human
  review.

#### Scenario: export is deterministic

- GIVEN the same report directory
- WHEN atlas export runs repeatedly
- THEN the JSON node and edge ordering SHALL be stable.
