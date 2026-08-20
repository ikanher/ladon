## ADDED Requirements

### Requirement: Recursive lineage traversal uses the selected directional access path
Every recursive lineage step SHALL keep the frontier row outermost and search `lineage_edges` by `(closure_id, source)` for dependency traversal or `(closure_id, target)` for reverse traversal, with optional edge kind applied through the same covering path.

#### Scenario: Populated forward closure is explained
- **WHEN** the portable high-fan-out closure is queried in the forward direction
- **THEN** `EXPLAIN QUERY PLAN` identifies the forward covering index with both `closure_id` and `source` and contains no closure-wide edge scan

#### Scenario: Populated reverse closure is explained
- **WHEN** the same closure is queried in reverse
- **THEN** the plan identifies the reverse covering index with both `closure_id` and `target`

### Requirement: Acquisition work obeys finite query bounds
Depth, recursive-row, node, edge, and route limits SHALL constrain SQL acquisition before projection; output trimming alone MUST NOT be presented as a work bound.

#### Scenario: Closure has combinatorial path growth
- **WHEN** traversal reaches the recursive-row cap
- **THEN** execution terminates, reports truncation and the binding cap, and does not continue enumerating discarded paths

### Requirement: Warm closure summary avoids route enumeration
The lineage CLI SHALL expose a summary view using aggregate/indexed SQL without recursive path enumeration and SHALL report closure identity, authority, freshness, nodes, edges by kind/ownership, trust boundaries, SCCs, omissions, bytes when available, and elapsed time.

#### Scenario: Stored closure is fresh
- **WHEN** a caller requests the summary with `--refresh never`
- **THEN** Ladon returns the bounded summary without invoking Lean or the recursive route query

### Requirement: Warm traversal has a relative latency gate
On the same portable populated fixture, the corrected bounded traversal SHALL be at least twenty times faster than the captured closure-scan baseline or complete within one second, whichever predicate is less strict for the host.

#### Scenario: Host performance varies
- **WHEN** absolute timing differs across machines
- **THEN** acceptance compares same-host runs with identical fixture and query fingerprints
