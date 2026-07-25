## ADDED Requirements

### Requirement: Future tactic-skeleton and InfoTree evidence contract

Ladon SHALL reserve future proof-xray work for optional tactic-skeleton and
InfoTree/proof-shape evidence with explicit authority labels and nonclaims.

#### Scenario: Tactic skeleton has backend metadata

- **WHEN** tactic skeleton evidence is reported
- **THEN** it SHALL include backend, version, source-artifact, and confidence metadata and SHALL be labeled as an inspection aid

#### Scenario: Direct declaration facts are consumed

- **WHEN** proof-xray consumers need statement, type/value dependency, axiom, sorry, or unsafe facts
- **THEN** they SHALL consume `ladon-elaborated-declaration-surface` output rather than defining a parallel extractor

#### Scenario: Quoted witness rows are consumed

- **WHEN** a proof-xray consumer displays quoted trust-footprint witness data
- **THEN** it SHALL preserve the `ladon-proof-xray-staging` backend, authority, source-artifact, and theorem-truth nonclaim

#### Scenario: Native generation is not assumed

- **WHEN** no separately approved tactic/InfoTree backend exists
- **THEN** the roadmap SHALL NOT claim native proof-xray generation, replay, theorem truth, proof correctness, or a complete proof-dependency graph
