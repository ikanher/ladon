## ADDED Requirements

### Requirement: Supported obligation DAGs have normalized graph identity
The system SHALL normalize versioned `proof_ir_v2_obligation_dag` artifacts into
artifact-owned DAG, imported-fact, obligation, produced-fact, authority, and
directed use/produce edge rows.

#### Scenario: Mixed CDC DAG
- **WHEN** a valid DAG contains imported facts, 22 obligations, produced facts, and mixed statuses
- **THEN** every node and edge is stored once with its exact DAG ID, kind, status, authority, description, and caveat evidence

#### Scenario: Missing edge endpoint
- **WHEN** an obligation uses a fact that is neither imported nor produced in the same DAG
- **THEN** ingestion rejects or explicitly omits the malformed edge according to the adapter contract and never creates a dangling graph edge

#### Scenario: Conflicting duplicate node
- **WHEN** the same node ID appears with conflicting kinds, statuses, or authorities
- **THEN** the artifact fails semantic normalization with a conflict diagnostic

### Requirement: DAG check witnesses remain separate quoted evidence
The system SHALL normalize the supported DAG check-witness kind as a separate
artifact and SHALL relate it to a DAG only through matching explicit DAG and
source-artifact identities.

#### Scenario: Exact validated witness
- **WHEN** a check witness names the cataloged DAG and reports its established and conditional obligation sets
- **THEN** the relation and quoted checker guarantee are stored without promoting any DAG node or Lean theorem status

#### Scenario: Stale witness target
- **WHEN** a witness path or hash identifies different DAG bytes
- **THEN** the witness remains cataloged, its relation is stale/unmatched, and it validates no active DAG generation

### Requirement: Obligation routes are SQL-first and authority-preserving
The system SHALL query forward and reverse reachability, minimum depth, and
bounded representative routes with parameterized recursive SQL while carrying
every traversed obligation's status and authorities.

#### Scenario: External conditional CDC route
- **WHEN** the caller asks for routes from `src.cdc.nowhere_zero_integer_eight_flow` to `claim.cdc.every_bridgeless_graph_has_cover`
- **THEN** the result includes the conditional background and global-conclusion obligations and does not label the route Lean-established

#### Scenario: Lean-premise CDC route
- **WHEN** the caller asks for routes from `hyp.cdc.oriented_integer_8_flow` to the same conclusion
- **THEN** representative routes preserve established intermediate obligations and the transition to the conditional global conclusion

#### Scenario: Reverse route
- **WHEN** the caller traverses backward from a produced claim
- **THEN** imported facts and obligations are returned in deterministic reverse-depth order under the same authority labels

### Requirement: Cycles and expansion are bounded honestly
The system SHALL terminate on cyclic input and enforce explicit maximum depth,
nodes, edges, routes, and output bytes with deterministic truncation metadata.

#### Scenario: Cyclic fixture
- **WHEN** a normalized DAG contains a reachable cycle
- **THEN** traversal terminates, reports the cycle or repeated reference, and does not repeatedly expand the same path state

#### Scenario: Route cap reached
- **WHEN** a diamond-rich graph has more routes than the configured maximum
- **THEN** the result returns deterministic representative routes and reports truncation plus the controlling cap

### Requirement: DAG lookup paths are indexed and isolated
The system SHALL provide and validate exact forward/reverse graph indexes, node
identity/status indexes, DAG-generation indexes, and checker-target indexes,
and SHALL keep ProofIR graph rows outside Lean lineage tables.

#### Scenario: Forward and reverse query plans
- **WHEN** forward and reverse edge lookups are explained
- **THEN** SQLite uses the prescribed `(dag, source, kind, target)` and `(dag, target, kind, source)` indexes

#### Scenario: No lineage contamination
- **WHEN** a conditional ProofIR route and a Lean theorem lineage closure coexist
- **THEN** no ProofIR node or edge appears in `lineage_nodes` or `lineage_edges`
