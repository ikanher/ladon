## ADDED Requirements

### Requirement: Constrained lineage schema
The private proof-search database SHALL store theorem closures, endpoint nodes,
typed edges, trust facts, SCC membership, and omissions in normalized tables with
foreign keys, uniqueness checks, enumerated status checks, and required lookup
indexes.

#### Scenario: Edge endpoints are constrained
- **WHEN** an ingestion transaction attempts to insert an edge whose source or target is absent from the same closure
- **THEN** the database rejects the transaction and retains the previous active closure

#### Scenario: Both traversal directions are indexed
- **WHEN** schema introspection examines lineage edges
- **THEN** it finds declared indexes beginning with closure/source/kind and closure/target/kind in the documented column order

### Requirement: Complete authoritative ingestion
The ingestion service MUST accept actual-proof lineage only from a compatible
theorem plan whose semantic graph is complete and whose authority is
`lean_environment`. It MUST independently validate counts, endpoint coverage, and
the semantic closure fingerprint.

#### Scenario: Complete theorem plan is accepted
- **WHEN** a valid complete theorem plan is ingested into a compatible fresh index
- **THEN** every local and frontier endpoint, type/value edge, SCC member, and trust fact is stored under one closure identity

#### Scenario: Partial plan is rejected
- **WHEN** semantic status, helper completion, counts, checksum, or closure fingerprint is partial or inconsistent
- **THEN** ingestion fails without storing or activating any row from that plan

### Requirement: Typed external frontier nodes
Every edge endpoint MUST have a lineage-node row. Targets outside the local semantic
node collection SHALL be stored as explicit external-frontier nodes using the
planner's owner, kind, axiom, unsafe, and availability evidence without fabricated
source locations.

#### Scenario: External axiom endpoint
- **WHEN** a complete plan contains a value edge to an external declared axiom
- **THEN** the closure stores an external frontier node, the typed edge, and the corresponding trust fact with unavailable source status if no source evidence exists

### Requirement: Transactional closure replacement
Ingestion SHALL atomically publish one active closure per theorem and generation.
Failure at validation, insertion, constraint checking, size enforcement, integrity
checking, or commit MUST leave the prior active closure byte-for-byte queryable.

#### Scenario: Replacement succeeds
- **WHEN** a fresh compatible closure for an already indexed theorem passes all gates
- **THEN** one transaction activates the new identity and removes the superseded closure and its cascading child rows

#### Scenario: Replacement exceeds size ceiling
- **WHEN** the candidate closure would exceed the configured database size ceiling
- **THEN** ingestion reports the limit and preserves the prior database and active closure

### Requirement: Lineage identity and freshness
Each closure SHALL retain theorem, plan, semantic closure, source inventory,
configuration, schema, toolchain, helper, and base-index generation identities.
Status inspection MUST distinguish absent, fresh, stale-source, stale-configuration,
stale-toolchain, incompatible-schema, and corrupt evidence.

#### Scenario: Source changes after ingestion
- **WHEN** current source/configuration fingerprinting differs from the stored closure identity
- **THEN** status reports the specific stale class and the closure is not eligible for an authoritative lineage query

#### Scenario: Base index contains no lineage
- **WHEN** a compatible proof-search index has no stored theorem closure
- **THEN** lineage coverage reports unavailable with reason `not_ingested`, not a confirmed empty dependency graph
