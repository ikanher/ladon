## ADDED Requirements

### Requirement: Packet Evidence Profiles

Ladon SHALL classify packet evidence completeness under an explicit profile.

#### Scenario: review packet profile

- GIVEN a packet with metadata, tests, and owner references
- WHEN summarized with `review_packet`
- THEN the profile status SHALL be complete even if witness-bundle evidence is
  absent.

#### Scenario: witness bundle profile

- GIVEN a packet lacking witness JSON or checker scripts
- WHEN summarized with `witness_bundle`
- THEN the profile status SHALL be partial.

#### Scenario: generic compatibility

- GIVEN packet evidence is summarized
- WHEN callers inspect `status`, `score`, and `max_score`
- THEN the existing generic fields SHALL remain present.
