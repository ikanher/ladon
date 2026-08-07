## ADDED Requirements

### Requirement: Exact fresh closure selection
Every lineage query MUST select exactly one active closure by fully qualified theorem
name and compatible repository, schema, source, configuration, toolchain, helper,
and index identities before traversing any edge.

#### Scenario: Fresh closure is selected
- **WHEN** one active closure matches the theorem and all current identities
- **THEN** the query records that closure identity and performs traversal only within it

#### Scenario: Closure is stale or ambiguous
- **WHEN** no fresh compatible closure exists or more than one row claims to be active
- **THEN** the query returns a distinct stale, unavailable, or corrupt result and performs no fallback traversal

### Requirement: Indexed recursive SQL traversal
Forward dependency and reverse ancestry traversal SHALL use parameterized recursive
SQLite CTEs over the required closure/source and closure/target indexes with cycle
guards and finite depth and row ceilings.

#### Scenario: Trust-to-theorem ancestry
- **WHEN** a user selects a trust root and reverse lineage direction
- **THEN** SQL returns only nodes and typed edges connecting that root to the exact theorem within the selected closure and bounds

#### Scenario: Cyclic component is present
- **WHEN** the selected closure includes a cyclic SCC
- **THEN** traversal terminates deterministically without revisiting the component indefinitely and preserves SCC evidence

### Requirement: Bounded representative routes
The query service SHALL compute reachable nodes and minimum depths before
materializing a deterministic bounded set of representative predecessor chains. It
MUST NOT enumerate all simple paths as an intermediate operation.

#### Scenario: Diamond graph has several routes
- **WHEN** more root-to-target paths exist than `max_routes`
- **THEN** the service returns the deterministically ordered prefix, marks routes truncated, and reports a known lower bound without claiming a total path count

#### Scenario: Shortest spine requested
- **WHEN** one shortest representative route is requested for each trust root
- **THEN** ties are resolved by stable edge-kind and declaration-name ordering and repeated runs return identical rows

### Requirement: SQL-owned filters and joins
The query service SHALL express edge kind, root boundary, explicit roots, generated
inclusion, owner module/package, direction, and source-location joins in
parameterized SQL against the selected closure.

#### Scenario: Value-only query
- **WHEN** `edge-kind=value` is selected
- **THEN** returned routes contain only value-dependency edges and record the filter in the result identity

#### Scenario: Project boundary query
- **WHEN** project roots are selected
- **THEN** SQL derives project-owned boundary nodes from stored ownership evidence and source-links declarations where indexed source evidence exists

### Requirement: Query-plan and bound evidence
The service MUST expose applied depth, node, edge, route, recursive-row, time, and
result-size limits plus truncation and omission reasons. Schema tests MUST verify
representative lineage SQL uses the named access-path indexes.

#### Scenario: Depth cap stops traversal
- **WHEN** a route continues beyond `max_depth`
- **THEN** the result marks depth truncation and does not represent the missing target or route as absent from the complete closure

#### Scenario: Query plan regresses to a table scan
- **WHEN** a representative forward or reverse traversal no longer uses its required lineage-edge index
- **THEN** the focused query-plan gate fails before release
