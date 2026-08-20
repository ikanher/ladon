## ADDED Requirements

### Requirement: Typed evidence observations
Every semantic evidence record SHALL identify its producer, subject, environment, observation kind, result, guarantee scope, authority basis, limitations, and supporting artifact.

#### Scenario: Successful process without subject guarantee
- **WHEN** a check run exits successfully but names no checked subject or guarantee scope
- **THEN** it remains a process observation and is not classified as semantic acceptance

### Requirement: Orthogonal evidence dimensions
Assertion state, semantic validation, freshness, attachment result, replay relationship, coverage, authority basis, and guarantee scope SHALL remain independently represented.

#### Scenario: Fresh source with unchecked claim
- **WHEN** an exact fresh attachment refers to an unchecked producer assertion
- **THEN** the result reports exact attachment and fresh source without reporting semantic acceptance

### Requirement: Exact checker observations
Accepted checker observations SHALL include checker identity, executable or implementation identity, environment, exact inputs, operation, per-subject results, output digests, bounds, and guarantee.

#### Scenario: Lean declaration accepted
- **WHEN** a pinned Lean worker confirms one declaration in one environment
- **THEN** the observation's guarantee applies only to that declaration and environment

### Requirement: Population-scoped coverage
Coverage SHALL name a population kind and selector and report universe knowledge, expected, discovered, decoded, valid, projected, query-matched, omitted, and bounded populations.

#### Scenario: Theorem-specific absence
- **WHEN** a theorem dossier matches no surfaces but repository-wide ProofIR tables are nonempty
- **THEN** coverage reflects the theorem selector and does not infer observed-absent from whole-table counts

### Requirement: Stable limitations
Human-readable nonclaims SHALL be paired with stable limitation identifiers.

#### Scenario: Navigation path is rendered
- **WHEN** a navigation path is returned from a derivation graph
- **THEN** the result includes a stable limitation stating that the path is not a complete proof slice
