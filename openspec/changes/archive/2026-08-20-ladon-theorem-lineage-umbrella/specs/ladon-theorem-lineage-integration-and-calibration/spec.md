## ADDED Requirements

### Requirement: Portable end-to-end lineage fixtures
The test suite SHALL include a portable Lean fixture whose authoritative theorem
plans exercise chains, diamonds, shared trust roots, type/value edges, external
frontiers, compiler-generated nodes, SCC handling where supported, and no-declared-
axiom closures through ingestion, SQL, projection, and installed CLI layers.

#### Scenario: Diamond fixture completes end to end
- **WHEN** the fixture theorem is planned, ingested, queried, and rendered
- **THEN** every returned route is edge-valid, shared nodes retain one identity, bounds are explicit, and text/JSON target and route facts agree

#### Scenario: Handwritten graph disagrees with Lean
- **WHEN** expected semantic edges are not produced by the authoritative fixture helper
- **THEN** the test is corrected or rejected rather than overriding Lean evidence with a fabricated graph

### Requirement: Failure and preservation matrix
Portable tests MUST cover missing/incompatible indexes, absent and stale closures,
partial/checksum-invalid plans, dangling endpoints, transaction failure, corrupt DB,
all output/traversal caps, timeout, interruption, and resource limits.

#### Scenario: Ingestion fails after a valid generation
- **WHEN** a replacement hits a constraint, integrity, size, or interruption failure
- **THEN** the prior closure remains active and returns the same query identity and rows

#### Scenario: Query is capped
- **WHEN** a portable wide graph crosses route or recursive-row limits
- **THEN** the command succeeds with deterministic bounded rows and explicit controlling-cap evidence

### Requirement: Fingerprinted large-repository calibration
Acceptance SHALL run observational lineage measurements on the existing Quux CDC
theorem and at least two index-discovered Matrix-Factorization theorems. Records MUST
include repository/source/toolchain/index/plan/closure identities, graph and DB sizes,
ingestion time, warm SQL time, projection time, full CLI time, and peak memory where
available.

#### Scenario: Quux CDC calibration
- **WHEN** the known CDC theorem is calibrated
- **THEN** returned trust routes include edge-valid ancestry for observed `Classical.choice` and `propext` roots or record an identity-scoped explanation for any changed frontier

#### Scenario: Matrix-Factorization checkout changes
- **WHEN** source identity differs from a prior measurement
- **THEN** Ladon records a new observation and does not compare timings or routes as if the inputs were identical

### Requirement: Result-quality gates
Integration checks SHALL verify exact theorem endpoints, selected-root starts,
edge-contiguous routes, preserved type/value kinds, project source links where
available, stable ordering, bottleneck validity, and honest omissions. Sibling
repositories MUST NOT be the sole correctness oracle.

#### Scenario: Reported bottleneck is avoidable
- **WHEN** a selected-subgraph route reaches the theorem without crossing a claimed bottleneck
- **THEN** the integration gate fails

#### Scenario: Alternative-proof wording appears
- **WHEN** maintained output, docs, or skills imply exhaustive possible proofs
- **THEN** the language/evidence-boundary gate fails

### Requirement: Maintained documentation and skill
README, CLI documentation, help, and the authoritative Ladon skill SHALL teach the
same database-first theorem-lineage workflow, refresh semantics, common filters,
bounds, generated-index location, and actual-proof-versus-alternative-proof
distinction using current CLI flags.

#### Scenario: Maintained examples are checked
- **WHEN** documentation/skill drift tests run
- **THEN** active lineage commands parse with the installed CLI and contain no removed build or output flags

### Requirement: Full acceptance gate
The packet MUST run focused lineage tests, all proof-search/theorem-capsule
regressions, strict Python quality, deterministic fixture checks, installed-wheel
checks, OpenSpec strict validation, DB integrity/foreign-key/index/query-plan checks,
and `git diff --check` before the umbrella closes.

#### Scenario: Existing capsule behavior regresses
- **WHEN** theorem plan, materialize, replay, or extract compatibility tests fail
- **THEN** lineage integration is not accepted even if its focused tests pass
