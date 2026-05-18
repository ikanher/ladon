## ADDED Requirements

### Requirement: Atlas Reviewer Cards

Ladon SHALL emit compact reviewer cards derived from atlas graph rows.

#### Scenario: card includes review routing fields

- GIVEN an atlas contains report, finding, and review-region nodes
- WHEN reviewer cards are rendered
- THEN each card SHALL include root, backend, top findings, review regions,
  strongest evidence, known non-claims, and source report links.

#### Scenario: missing evidence is explicit

- GIVEN an atlas does not contain packet evidence or non-claim data
- WHEN reviewer cards are rendered
- THEN the card SHALL state that those fields are not recorded in the atlas.
