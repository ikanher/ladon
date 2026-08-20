## ADDED Requirements

### Requirement: Operational Atlas Suite

Ladon SHALL evolve static atlas exports into operational review artifacts that
are queryable, diffable, and suitable for reviewer triage.

#### Scenario: umbrella tracks child packets

- GIVEN the operational atlas suite is active
- WHEN a child packet is selected
- THEN the umbrella SHALL name the child packet and the operational question it
  is expected to answer.

#### Scenario: queryable atlas surface

- GIVEN a report atlas has been generated
- WHEN the SQLite query child is complete
- THEN Ladon SHALL provide a deterministic derived query surface with canned
  queries for hotspot, recurrence, region-shift, and proof-pressure questions.

#### Scenario: atlas diff surface

- GIVEN two report atlas roots are available
- WHEN the diff child is complete
- THEN Ladon SHALL report added, removed, and changed operational signals
  without requiring manual JSON inspection.

#### Scenario: reviewer cards

- GIVEN a report atlas is available
- WHEN the reviewer-card child is complete
- THEN Ladon SHALL emit compact root/report cards containing top findings,
  review regions, evidence, non-claims, and source report links.

### Requirement: OpenSpec Hygiene Self-Audit

Ladon SHALL be able to detect misleading packet metadata that disagrees with
task evidence.

#### Scenario: active packet appears complete

- GIVEN an OpenSpec change has all task checklist items complete
- AND its metadata status is still `active`
- WHEN packet hygiene analysis runs
- THEN Ladon SHALL flag the status drift as an operational hygiene finding.
