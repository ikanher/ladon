## ADDED Requirements

### Requirement: Proof-search dispatch is lightweight
The installed entrypoint SHALL inspect the selected command family before importing the general analyzer or optional ProofIR modules and SHALL preserve public help, streams, signals, and exit codes.

#### Scenario: One-shot proof-search help
- **WHEN** installed `ladon proof-search --help` is measured against the preregistered baseline
- **THEN** startup overhead is reduced by at least 50 percent on the same benchmark host without contract drift

### Requirement: Existing graph queries are set-oriented
Lineage route materialization SHALL reuse one bounded traversal acquisition, and boundary metadata and ProofIR path nodes SHALL be fetched in bounded set-oriented queries.

#### Scenario: Route count grows
- **WHEN** a fixture returns more routes or path nodes within the configured cap
- **THEN** trace assertions show no per-route boundary query and no per-node materialization query

### Requirement: Optimization preserves answers
The optimized implementation MUST remain contract-equivalent to the baseline for ordering, authority, bounds, omissions, and endpoint semantics.

#### Scenario: Baseline fixture is replayed
- **WHEN** every existing lineage and ProofIR contract fixture is run through optimized code
- **THEN** all public semantic predicates remain unchanged
