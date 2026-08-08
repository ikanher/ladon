## ADDED Requirements

### Requirement: Obligation routes reach the requested endpoint
The system SHALL return only paths that begin at the selected start node and end at the selected end node in the requested direction.

#### Scenario: Forward chain
- **WHEN** a caller selects the first and last nodes of a three-edge chain
- **THEN** every returned path contains the ordered three-edge route and terminates at the requested end

#### Scenario: Unreachable endpoint
- **WHEN** the end node is not reachable under the selected direction and bounds
- **THEN** no route is returned and the result distinguishes unreachable from truncated search

#### Scenario: Reverse route
- **WHEN** the caller requests reverse traversal from a produced claim to an imported premise
- **THEN** every returned path follows stored edges backward and terminates at that premise

### Requirement: Representative paths and trees are shortest and deterministic
The system SHALL compute minimum depth, return bounded representative shortest paths in stable order, and construct a deduplicated selected tree/subgraph from those paths.

#### Scenario: Diamond DAG
- **WHEN** two equal-depth paths connect the same endpoints
- **THEN** both are returned under the cap in deterministic order and shared nodes appear once in the selected subgraph

#### Scenario: Route cap
- **WHEN** more shortest paths exist than the route cap
- **THEN** deterministic representatives are returned with explicit truncation and observed/allowed counts

### Requirement: Routes preserve obligation and authority transitions
The system SHALL return each traversed edge, obligation identity, node kind, node status, and authorities and SHALL summarize boundary transitions without ranking or flattening them.

#### Scenario: Established to conditional boundary
- **WHEN** a route crosses from Lean-established premises to an external conditional conclusion
- **THEN** the transition is explicit and the route is not labeled Lean-established

### Requirement: Cycles and expansion terminate honestly
The system SHALL terminate cyclic traversal using visited state and enforce maximum depth, states, nodes, edges, routes, and output bytes.

#### Scenario: Reachable cycle
- **WHEN** a route search encounters a cycle before the endpoint
- **THEN** it terminates, records the repeated reference/cycle, and returns any endpoint paths found within bounds

### Requirement: Route SQL uses the stored graph indexes
The system SHALL use the registered forward and reverse DAG edge indexes for traversal entry and SHALL never insert ProofIR graph rows into Lean lineage tables.

#### Scenario: Explained route entry
- **WHEN** forward and reverse route entry queries are explained
- **THEN** the prescribed ordered indexes appear in the query plans
