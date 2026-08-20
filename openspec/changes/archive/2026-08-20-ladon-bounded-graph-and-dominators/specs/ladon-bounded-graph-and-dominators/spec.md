## ADDED Requirements

### Requirement: Graph traversal is pure and bounded
The system SHALL provide deterministic forward/reverse expansion, cycle-safe paths, SCCs, and shared/cycle-aware DAG unfolding over supplied rows with explicit node, edge, depth, path, and output bounds.

#### Scenario: Cyclic diamond is traversed
- **WHEN** a bounded fixture contains sharing and a back edge
- **THEN** traversal terminates deterministically and records shared, cycle, and cap omissions without inventing edges

### Requirement: Dominators are correct and scalable
The system SHALL compute dominators with a near-linear algorithm and stable multiple-root/disconnected semantics.

#### Scenario: Generated graph is checked
- **WHEN** a deterministic small graph is evaluated
- **THEN** its dominators equal a brute-force oracle for all reachable nodes

### Requirement: Database adapters preserve contracts
SQLite-backed lineage and ProofIR adapters MUST limit row acquisition before invoking pure algorithms and MUST preserve external node identities and result ordering.

#### Scenario: Adapter cap is reached
- **WHEN** acquired rows reach a configured cap
- **THEN** the public result is bounded and identifies the acquisition omission
