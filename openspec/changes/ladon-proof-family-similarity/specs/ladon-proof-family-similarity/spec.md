## ADDED Requirements

### Requirement: Deterministic Proof-Family Similarity Candidates

Ladon SHALL expose deterministic proof-family similarity candidates in
declaration graph reports.

#### Scenario: high-similarity family

- GIVEN two declarations with a shared suffix and strongly overlapping resolved
  references or unresolved-reference class profiles
- WHEN the declaration graph is summarized
- THEN Ladon SHALL emit a proof-family similarity candidate row.

#### Scenario: low-similarity family

- GIVEN two declarations with a shared suffix but low reference/profile overlap
- WHEN the declaration graph is summarized
- THEN Ladon SHALL not emit a proof-family similarity candidate row.

#### Scenario: text report wording

- GIVEN proof-family similarity candidates exist
- WHEN the text renderer runs
- THEN the report SHALL describe them as "similar proof-family candidate".
