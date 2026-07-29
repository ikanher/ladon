## ADDED Requirements

### Requirement: Caller-neutral theorem planning command
The installed Ladon CLI SHALL provide a caller-neutral theorem planning operation
that accepts a repository root, one fully qualified declaration name, and an
explicit output/representation choice. Planning MUST be read-only with respect to
the target repository and MUST preserve the existing analyzer CLI contract.

#### Scenario: Human plans a theorem capsule
- **WHEN** a user invokes the installed theorem planning command with a valid repository and fully qualified theorem name
- **THEN** Ladon emits the selected plan representation and does not create or modify files inside the repository

#### Scenario: Existing analyzer invocation remains valid
- **WHEN** a caller uses an analyzer invocation that predates theorem capsules
- **THEN** Ladon preserves its established parsing, output-channel, and exit semantics

### Requirement: Lean-authoritative exact theorem selection
The planner MUST use the repository's pinned Lean environment to confirm the exact
fully qualified name, declaration kind, owning module, and source command selected
for extraction. Lexical source evidence MAY nominate candidates but MUST NOT be the
final identity authority.

#### Scenario: Exact theorem is confirmed
- **WHEN** lexical ownership and the pinned Lean environment agree on one theorem and source command
- **THEN** the plan records the Lean-confirmed identity, kind, module, source range, selection range, and authority

#### Scenario: Short or ambiguous name is supplied
- **WHEN** the requested name is not a unique fully qualified theorem in the pinned Lean environment
- **THEN** planning fails with structured not-found, ambiguous, or wrong-kind evidence and publishes no valid plan

#### Scenario: Source and environment disagree
- **WHEN** the lexical candidate does not match the declaration confirmed by Lean
- **THEN** planning reports the disagreement and MUST NOT guess an owner or command boundary

### Requirement: Complete semantic dependency protocol
The planner SHALL obtain every reachable type constant, proof-value constant when
available, compiler-generated auxiliary, and trust fact through a versioned exact
protocol. The protocol MUST provide an explicit completion witness and MUST NOT
consume a bounded report projection as completeness evidence.

#### Scenario: Dependency closure exceeds report bounds
- **WHEN** a theorem has more dependencies than a human-facing declaration row can retain
- **THEN** the plan still records the complete reachable semantic closure without truncating it to the report bound

#### Scenario: Stream is partial or incompatible
- **WHEN** an end marker, declared count, checksum, required value record, or protocol version is missing or inconsistent
- **THEN** planning fails closed with a partial-or-incompatible status and publishes no closure-complete plan

#### Scenario: Semantic cycle is reachable
- **WHEN** reachable generated or mutually related declarations form a cycle
- **THEN** the planner preserves the typed edges and represents the cycle deterministically as a strongly connected component

### Requirement: Separate semantic and build closures
The plan MUST contain distinct typed semantic and build graphs. The semantic graph
MUST distinguish type, value, generated/auxiliary, and trust relationships. The
build graph MUST account for repository modules, imports, source roots, package
ownership, toolchain/configuration inputs, locked external packages, and declared
resources.

#### Scenario: Imported module has no selected declaration node
- **WHEN** a module is required by the import graph but contributes no declaration selected by the semantic closure
- **THEN** it remains in the build closure with an import-based inclusion reason

#### Scenario: External declaration is reachable
- **WHEN** a semantic dependency is owned by a locked external package
- **THEN** the semantic graph retains the declaration frontier and the build graph links it to the package and lock evidence without claiming the source is repository-owned

### Requirement: Exact source and configuration boundaries
The plan MUST record the target source prefix boundary as the exact end of the
parser command associated with the Lean-confirmed theorem. It MUST fingerprint all
repository-owned source files and toolchain, Lake, manifest, source-root, and module
DAG inputs needed by materialization.

#### Scenario: Theorem is nested in contextual commands
- **WHEN** the theorem follows namespace, section, variable, option, notation, attribute, or local-instance commands
- **THEN** the planned prefix begins at byte zero and ends at the theorem command boundary so preceding context is retained

#### Scenario: Repository changes during planning
- **WHEN** any bound source or configuration input changes between planning observations
- **THEN** Ladon diagnoses snapshot drift and publishes no valid plan

### Requirement: Deterministic plan and compatibility contract
The canonical JSON plan SHALL be schema-versioned, protocol-versioned,
toolchain-scoped, canonically ordered, and byte-stable for identical inputs. It
MUST include repository-relative normalized paths, hashes, graph coverage,
guarantee level, nonclaims, and enough identity for materialization to reject a
stale or incompatible plan.

#### Scenario: Identical repository is planned twice
- **WHEN** the same theorem and unchanged inputs are planned twice with the same Ladon and Lean protocol versions
- **THEN** the canonical plans have the same semantic identity and bytes

#### Scenario: Materializer cannot understand a plan
- **WHEN** a consumer does not support the plan schema, helper protocol, toolchain fingerprint algorithm, or guarantee level
- **THEN** the plan contract requires rejection rather than best-effort interpretation

### Requirement: Explicit trust and unsupported frontiers
The planner MUST distinguish observed trust facts, locked external frontiers,
unsupported dynamic/native/build facets, and unknown evidence. Unknown or
unsupported facets MUST NOT be represented as absent or closure-complete.
Planning MUST NOT execute arbitrary target-controlled build initializers solely to
discover hidden inputs.

#### Scenario: Native plugin or dynamic resource is required
- **WHEN** planning observes a native plugin, unsafe external path, custom dynamic build action, or undeclared resource that v1 cannot package
- **THEN** the plan records an unsupported facet and is ineligible for an unqualified locked/rebuildable capsule

#### Scenario: Axiom or admitted declaration is reachable
- **WHEN** Lean reports a trust-relevant dependency in the theorem closure
- **THEN** the plan records that trust frontier without claiming axiom freedom or theorem falsity
