## Purpose

Expose the complete stored compiled dependency graph within declared resource
and library boundaries, independently of bounded representative proof routes.

## ADDED Requirements

### Requirement: Stored closure projection
Ladon SHALL provide `theorem lineage --view closure` over one exactly selected
stored closure. With sufficient node, edge and byte budgets, it MUST return every
selected distinct node and typed edge without enumerating dependency paths.

#### Scenario: Many paths in a small graph
- **WHEN** a layered diamond has exponentially many paths but its stored nodes and edges fit the requested budgets
- **THEN** the closure view returns each selected node and typed edge exactly once and reports complete selected-graph coverage independently of `max_routes`

#### Scenario: Single-node closure
- **WHEN** a valid selected closure contains only its target and no dependencies
- **THEN** the target is returned and zero edges is a complete result

### Requirement: Separate graph and route acquisition
Reachability for route-oriented views MUST discover distinct reachable nodes and
minimum depths before constructing a bounded set of representative routes. It
MUST NOT enumerate all simple paths as an intermediate operation. Shared nodes
MUST NOT consume reachability budget once per incoming path.

#### Scenario: Shared subproofs exceed the old path cap
- **WHEN** shared dependencies create more than 10,000 possible path prefixes while the distinct reachable graph fits the graph budgets
- **THEN** reachability remains complete and any route-limit truncation is reported only for the representative-route population

### Requirement: Explicit completeness dimensions
Results MUST distinguish source-closure extraction, selected-graph coverage,
representative-route coverage and external-boundary scope. Completion of one
MUST NOT imply completion of the others or theorem verification. Unknown coverage
MUST remain unknown.

#### Scenario: Complete extraction with a small display budget
- **WHEN** the source closure is complete but the selected projection exceeds its node budget
- **THEN** the result retains complete source-extraction status and reports incomplete selected-graph coverage with the controlling budget

#### Scenario: Project closure ends at library declarations
- **WHEN** every project-owned dependency is expanded and library declarations remain external frontier nodes
- **THEN** the result identifies that frontier explicitly and does not claim transitive expansion to all library axioms

### Requirement: Exact typed identity and counts
The closure view MUST preserve declaration identities and distinguish type from
value edges. Returned-node and typed-edge counts MUST equal their actual payload
populations. Route occurrences and deduplicated edge pairs MUST use different
labels and MUST NOT substitute for typed-edge counts.

#### Scenario: One pair has two edge kinds
- **WHEN** the same dependency pair occurs in both a type and a proof value
- **THEN** the closure view retains both typed edges, while any untyped pair count reports one separately

### Requirement: Stable finite caps and closed endpoints
All views MUST obey declared node, edge, depth where applicable, and output-byte
limits. A capped graph MUST have no dangling edge endpoints. Cap detection MUST
use an observed extra item or an exact selected-population count; equality with a
cap alone MUST NOT imply truncation. Output failure MUST preserve prior output.

#### Scenario: Exactly at the node limit
- **WHEN** the full selected graph has exactly the permitted node count and fits its other limits
- **THEN** the result reports complete selected-graph coverage

#### Scenario: Edges exceed the output budget
- **WHEN** selected edges or serialized output exceed their corresponding budget
- **THEN** Ladon reports the specific truncation or output error without publishing a malformed or falsely complete graph

#### Scenario: Reachable nodes exist past the depth boundary
- **WHEN** a route query reaches its depth cap and an eligible unseen dependency remains
- **THEN** the result reports depth-limited reachability instead of claiming the dependency or route is absent

### Requirement: Filters and structural boundaries
Selections MUST report their edge-kind and generated-node policies. Excluded
nodes or edges MUST remain explicit selection omissions; Ladon MUST NOT invent
proof edges across removed nodes. Cyclic components MUST terminate and retain
membership evidence rather than being silently discarded to manufacture a DAG.

#### Scenario: A generated lemma joins two user declarations
- **WHEN** generated declarations are excluded
- **THEN** the selected graph reports the removed boundary and does not present a new direct compiled edge between the user declarations

#### Scenario: Recursive component
- **WHEN** the stored closure has a nontrivial SCC or a self-loop
- **THEN** the closure view preserves its evidence and route acquisition terminates without repeated unbounded expansion

### Requirement: Freshness and historical authority
Closure selection MUST reuse exact theorem, environment, source, configuration,
helper and index identity checks. Missing or stale data MUST fail closed without
lexical fallback. Historical selection MUST remain a stored historical observation
and MUST NOT claim a current environment match.

#### Scenario: Stored-only query
- **WHEN** `--refresh never` selects an existing compatible closure
- **THEN** projection performs no Lean or Lake invocation and does not mutate stored proof evidence

#### Scenario: Historical closure
- **WHEN** `--history` selects a preserved closure
- **THEN** the closure view reports its historical identity and coverage without upgrading freshness or execution authority

### Requirement: Compatible views and transparent options
Existing summary, graph, routes, spines, tree and bottleneck view meanings MUST
remain documented. The new closure view MUST be explicitly distinguishable from
a graph of representative routes. Inapplicable explicit selector options MUST
be rejected or reported as inapplicable, never silently presented as effective.

#### Scenario: Route graph remains bounded
- **WHEN** an existing client requests `--view graph` with a small route limit
- **THEN** it receives the documented representative-route graph with route coverage stated, rather than an undocumented larger payload

### Requirement: Deterministic bounded operation
Stored projections MUST use closure-scoped indexed queries and finite work limits.
Ordering and fingerprints MUST be deterministic for equivalent selected records.
The implementation MUST NOT use higher memory or database ceilings as the fix for
path-multiplicity growth.

#### Scenario: Reordered insertion
- **WHEN** equivalent nodes and typed edges are inserted in a different order
- **THEN** the same request returns the same canonical graph and selection fingerprint

#### Scenario: Increasing shared-path multiplicity
- **WHEN** a test adds sharing without a proportional increase in unique nodes and edges
- **THEN** reachability work is measured against unique graph work, not the exponential count of possible paths
