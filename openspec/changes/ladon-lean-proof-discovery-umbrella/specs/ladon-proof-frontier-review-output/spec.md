## ADDED Requirements

### Requirement: Declaration-level proof frontier
Ladon SHALL generate a deterministic source-linked frontier containing compiled
endpoints, immediate consumers, constructor fields, unmatched assumptions still
entering from callers, source/audit owners, and build/freshness status.

#### Scenario: Frontier from constructor work
- **WHEN** a reviewed constructor has compiled suppliers, restricted suppliers, and unmatched fields
- **THEN** the frontier represents each category separately with declaration and source fingerprints

### Requirement: Accepted and rejected route history
The frontier SHALL reference canonical accepted and rejected proof-route cards and
retain the reason and stage for every rejection.

#### Scenario: Unchanged rejected route
- **WHEN** two packet revisions contain the same rejected candidate fingerprints
- **THEN** the later frontier preserves the prior reason and identifies that no relevant route input changed

### Requirement: Declaration-surface revision comparison
Frontier comparison SHALL consume the existing theorem-surface changelog to report
type, premise, conclusion, source, dependency, proof-only, addition, removal, and
exact-identity changes separately from heuristic rename candidates.

#### Scenario: Added premise
- **WHEN** a compiled endpoint gains a premise between packet revisions
- **THEN** the frontier diff identifies the changed declaration surface and affected route cards rather than reporting only a changed file

### Requirement: Packet-evidence integration without authority promotion
Existing packet-evidence reports SHALL be able to consume a compact frontier while
preserving its backend, freshness, truncation, and theorem-authority nonclaims.

#### Scenario: Frontier quoted by packet report
- **WHEN** a review packet includes a valid frontier artifact
- **THEN** packet evidence summarizes its endpoints and gaps but does not call the mathematical proof verified or replay its Lean routes

### Requirement: Integrated proof-discovery acceptance scenarios
The umbrella exit SHALL include portable analogues of all six `TODO.md` discovery
questions and label any lexical or heuristic fallback explicitly.

#### Scenario: Six-scenario gate
- **WHEN** the proof-discovery acceptance harness runs
- **THEN** it covers all-state lane integrability and field coverage, all-row versus retained quantitative bounds, row-guard diagnosis, reverse primitive consumers and leakage, normalized-to-physical scale warning, and a current constructor-goal coverage matrix
