## ADDED Requirements

### Requirement: Dependency-safe coverage and integration milestones
The capability SHALL be delivered through an early `coverage-foundation`
milestone and a later `snapshot-and-region-integration` milestone. The
foundation SHALL define collection coverage, upstream omission, generic
registration, and snapshot identity contracts before dependent producer
capabilities implement their rows. Producer-aware stratification, inspection
actions, final source verification, multi-format integration, and integrity
review regions MUST NOT be treated as foundation prerequisites and SHALL be
completed only after their registered producer surfaces are available.
Producer capabilities SHALL close on their canonical registration rows and
ordinary inspection actions without depending on concrete review-region objects;
this capability exclusively synthesizes those objects during
`snapshot-and-region-integration`.

#### Scenario: Producer begins after the foundation
- **WHEN** the `coverage-foundation` milestone passes its portable contract gates
- **THEN** scope/join, declaration/audit, generated-family, and inspection capabilities can register canonical collections and authority against it without depending on final region or multi-render integration

#### Scenario: Integration resumes after producers
- **WHEN** all registered producer capabilities expose their canonical rows, strata, coverage, authority, and ordinary inspection actions
- **THEN** `snapshot-and-region-integration` composes those surfaces through the existing report, CLI, atlas, and review-region owners without creating a dependency cycle

### Requirement: Compositional collection coverage
Every bounded canonical report collection SHALL expose `visible`, `total`,
`omitted`, `totalKnown`, and `completeness` together with the population, scope,
and authority to which those values apply. When the owning analysis knows the
population cardinality, `total` and `omitted` SHALL be exact and SHALL satisfy
`total = visible + omitted`. When source failure or partial extraction makes the
population cardinality unknowable, `total` and `omitted` SHALL use the schema's
explicit unknown representation, `totalKnown` SHALL be false, and the collection
SHALL expose an observed lower bound. Counts and unknown states MUST compose
through summaries, projections, renderers, evidence links, review regions, and
report-set consumers, and omitted or unobserved evidence MUST NOT be represented
as an observed empty population.

#### Scenario: Bounded declaration collection
- **WHEN** a report exposes only a bounded subset of matching lexical declaration rows
- **THEN** the collection records its visible, total, and omitted counts, marks itself incomplete, and identifies the lexical population those counts describe

#### Scenario: Empty complete collection
- **WHEN** a completed analysis observes no rows for a collection and applies no upstream or projection omission
- **THEN** the collection reports zero visible, zero total, zero omitted, `totalKnown` true, and complete rather than reusing an unavailable or truncated state

#### Scenario: Source failure leaves the population unknown
- **WHEN** one selected source cannot be indexed and the analyzer cannot determine how many matching rows it would have contributed
- **THEN** the collection reports its visible rows and observed lower bound, marks `totalKnown` false and completeness partial, and does not use the observed count as a repository total or invent an omitted count

#### Scenario: Grouped report owner contains child evidence rows
- **WHEN** audit commands, resource directives, or lexical declarations are grouped beneath module-owned report containers and a projection retains only some parent and child rows
- **THEN** projected coverage counts the retained child evidence rows rather than the number of parent containers, and every emitted child `coverageRef` resolves to that registered collection

### Requirement: Honest projection completeness
Every report projection SHALL identify its projection policy, analysis
fingerprint, and all intentional and upstream omissions relevant to its exposed
collections. A `full` projection MUST mean that it introduces no intentional
projection omission; it MUST NOT claim complete evidence when extraction,
analysis, internal summarization, or another upstream cap omitted rows.

#### Scenario: Full projection inherits an internal cap
- **WHEN** the full renderer receives a declaration collection that was capped before projection
- **THEN** the projection identifies that collection as upstream-incomplete and lists its visible, total, omitted, and controlling-cap details

#### Scenario: Review projection intentionally bounds evidence
- **WHEN** review projection selects a bounded subset from otherwise complete canonical evidence
- **THEN** its omission metadata distinguishes intentional review selection from upstream analysis incompleteness

#### Scenario: Registered evidence route is unavailable
- **WHEN** a registered producer has a malformed, dangling, ambiguous, or capacity-incompatible canonical evidence route
- **THEN** review projection suppresses that producer and its signal atomically and records `projection_evidence_unavailable` rather than mislabeling the loss as an intentional collection limit

#### Scenario: Referenced owner lies beyond the initial review selection
- **WHEN** a valid producer references an unselected row in a stratum already at its review allowance
- **THEN** projection substitutes the referenced owner without exceeding the per-stratum allowance, copies no unreferenced nested population wholesale, and retains truthful nested omission metadata

#### Scenario: Embedded evidence owner lies beyond the review selection
- **WHEN** a retained import-boundary row references source-index membership evidence outside the initial bounded review selection
- **THEN** projection substitutes and rebases the exact membership owner within the same collection allowance so the emitted evidence route resolves without overstating coverage

### Requirement: Deterministic stratified review evidence
Review projection SHALL select bounded evidence through a documented,
deterministic stratification over evidence kind, severity, status, population,
and command or module role before stable tie-breaking. A generic alphabetic or
insertion-order first-N limit MUST NOT erase every representative of a present
stratum. Each stratum MUST expose its visible, total, omitted, and completeness
state.

#### Scenario: Audit rows sort after module rows
- **WHEN** a complete canonical report contains command-bearing audit surfaces that sort after more than one page of declaration-empty module rows
- **THEN** review projection retains a bounded audit representative and reports the audit stratum's total and omitted counts

#### Scenario: One stratum exceeds its allowance
- **WHEN** one evidence stratum contains more rows than its deterministic review allowance
- **THEN** Ladon bounds that stratum without consuming the required representation of other present strata

#### Scenario: Equivalent source order changes
- **WHEN** equivalent canonical evidence differs only in input insertion order
- **THEN** stratified review membership, stable ordering, coverage counts, and normalized projection bytes remain identical

### Requirement: Severity-aware text accounting
Compact text rendering SHALL summarize promoted findings in severity-aware order
and MUST account for every selected finding as displayed, summarized in another
named section, or omitted with an explicit count and inspection route. Text and
structured renderings MUST agree on selected counts, severity counts, authority,
and completeness.

#### Scenario: Errors and informational findings exceed the text limit
- **WHEN** selected error and informational findings together exceed the bounded text allowance
- **THEN** text prioritizes the documented severity ordering and reports displayed, elsewhere-rendered, and omitted counts without presenting informational rows as the complete finding surface

#### Scenario: Finding is rendered in an architecture section
- **WHEN** a selected finding is summarized outside the primary findings list
- **THEN** text accounting identifies that named section and does not count the row as silently omitted

### Requirement: Coverage-aware atlas ingestion and query
The existing installed report-set workflow SHALL propagate source collection
coverage, population, scope, authority, and analysis fingerprints into atlas
tables and derived query metadata. An atlas query that claims exhaustive results
MUST be unavailable when a required source table is incomplete unless the query
engine can prove the result is sound over the visible subset. Subset-only results
MUST be labeled and MUST NOT be presented as repository-wide absence.

#### Scenario: Exhaustive dependency query receives partial declarations
- **WHEN** atlas ingestion receives a declaration-dependency table with omitted rows and a caller requests an exhaustive dependency query
- **THEN** the query returns a structured incomplete-authority diagnostic naming the required table and its coverage instead of a false empty or exhaustive result

#### Scenario: Query is sound over visible rows
- **WHEN** a documented atlas query can return a useful bounded subset without assuming omitted rows are absent
- **THEN** it returns that subset with visible-source labeling, inherited coverage, and an explicit nonclaim of exhaustiveness

#### Scenario: Atlas inputs have incompatible fingerprints
- **WHEN** report-set ingestion receives tables whose analysis or source fingerprints cannot belong to one compatible input set
- **THEN** the existing workflow rejects or isolates the incompatible input and does not merge its authority into one atlas

### Requirement: One-analysis multi-format rendering
One ordinary CLI analysis invocation SHALL support rendering multiple requested
format/path outputs from one immutable canonical analysis result. Rendering MUST
NOT rediscover source, rerun an analysis phase, or start an additional Lean
helper for each format. Every output MUST carry the same analysis identity,
source fingerprint, scope, semantic counts, authority states, and completeness.
Output planning MUST reject more than one stdout destination and any mixing of
legacy output flags with canonical single- or multi-output options. It MUST also
reject duplicate requested formats, duplicate destination paths, and any
invocation that combines repeatable canonical `--emit FORMAT=PATH` with the
canonical single-output `--format`/`--output` pair. Every such conflict MUST fail
before source discovery or analysis begins.

#### Scenario: Text and JSON requested together
- **WHEN** a caller requests text and JSON outputs from one analysis invocation
- **THEN** Ladon executes source analysis once and renders both outputs from the same canonical result with equal analysis identity and semantic counts

#### Scenario: One output write fails
- **WHEN** analysis succeeds but one requested output path cannot be written
- **THEN** Ladon reports the established output failure for that destination, preserves the shared analysis identity for any successfully written output, and does not rerun analysis to retry rendering

#### Scenario: Multiple stdout destinations
- **WHEN** an invocation requests more than one rendered representation on stdout
- **THEN** Ladon rejects the invocation before analysis using the existing CLI invocation-error contract

#### Scenario: Legacy and canonical output options are mixed
- **WHEN** an invocation combines legacy dual-output flags with the canonical multi-format destination syntax
- **THEN** Ladon rejects the ambiguous invocation before analysis and emits no partial report

#### Scenario: Canonical single- and multi-output spellings are mixed
- **WHEN** an invocation combines any repeatable `--emit FORMAT=PATH` request with `--format` or `--output`
- **THEN** Ladon rejects the ambiguous invocation before discovery or analysis and writes no output

#### Scenario: Multi-output formats or paths are duplicated
- **WHEN** repeatable `--emit FORMAT=PATH` requests contain a duplicate format or duplicate destination path
- **THEN** Ladon rejects the output plan before discovery or analysis and identifies the duplicate conflict through the existing invocation-error contract

### Requirement: Captured source snapshot integrity
The pipeline SHALL create a manifest of every source-state and configuration
component required by the analysis contract and SHALL ensure that every analyzed
byte set matches the corresponding captured manifest fingerprint. It SHALL compare
the relevant repository state with that manifest after the last source-reading
phase. A per-read mismatch or final comparison mismatch MUST produce a structured
`source_changed_during_analysis` diagnostic, identify affected collections and
completeness, and prevent the result from claiming a stable complete snapshot.
The contract MUST NOT claim observation of transient filesystem events whose bytes
were neither analyzed nor present at the final comparison. All emitted formats
from one result MUST report the same snapshot state and analysis identity.

#### Scenario: Source changes during analysis
- **WHEN** a registered Lean source file changes and either analyzed bytes or the final registered state no longer match the captured manifest
- **THEN** Ladon records `source_changed_during_analysis`, marks affected evidence incomplete or unstable, and does not serialize any format as a stable complete snapshot

#### Scenario: Mixed-read source is rejected
- **WHEN** a source file's bytes no longer match the captured manifest when the analyzer is about to index or consume them
- **THEN** Ladon does not combine those bytes with rows from the captured snapshot and either restarts from one new manifest or records source drift and incomplete affected collections

#### Scenario: Transient unobserved change reverts
- **WHEN** a file changes and reverts without any mismatching bytes being analyzed and the final registered state matches the captured manifest
- **THEN** Ladon may report that analyzed bytes and final state match the manifest but does not claim that no transient filesystem event occurred

#### Scenario: Dirty source remains byte-stable
- **WHEN** the target is dirty before analysis but every analyzed byte set and the final registered source-state comparison match the captured manifest
- **THEN** Ladon may emit a stable snapshot using the recorded byte-level and configuration fingerprints while preserving the dirty-state observation separately

#### Scenario: Separate renders use one drift decision
- **WHEN** multiple formats are requested and final source verification detects drift
- **THEN** every format carries the same drift diagnostic, source fingerprints, affected coverage, and analysis identity

### Requirement: Integrity review-region routing
Review-region synthesis SHALL provide bounded regions for structurally joined
architecture evidence, declaration-collision candidates, audit surfaces,
generated-looking family candidates, and option or resource review surfaces when
those surfaces are present. Pressure labels in an option/resource region MUST come
only from normalized unlimited settings or explicit policy-backed classifications
owned by the inspection capability. Each region MUST link to canonical evidence and an ordinary
inspection operation, state authority and nonclaims, expose coverage, and MUST
NOT duplicate canonical payloads or create a theorem-correctness claim.

#### Scenario: Collision candidates are present
- **WHEN** namespace-aware lexical analysis emits declaration-collision candidates
- **THEN** the report includes a bounded collision review region with canonical row links, lexical authority, candidate nonclaims, and visible, total, and omitted counts

#### Scenario: No supported evidence exists for a region
- **WHEN** a completed selected population contains no supported rows for one integrity region
- **THEN** the report either omits that region with explicit routing metadata or marks it complete and empty without substituting an unrelated evidence family

#### Scenario: Region points to further inspection
- **WHEN** a review region omits member rows because of its bound
- **THEN** it provides a structured invocation of the same ordinary inspection CLI that can page through the canonical population

### Requirement: Coverage-preserving derived evidence
Every derived report surface SHALL retain typed references to the coverage and
authority of every source collection on which it depends, including summaries,
findings, aggregates, review regions, and atlas rows. A derived surface MUST be
suppressed, marked partial, or constrained to a subset-safe claim when omitted
upstream evidence could change its asserted meaning.

#### Scenario: Aggregate depends on a partial source table
- **WHEN** a resource-family aggregate is computed from a source table with omitted members
- **THEN** the aggregate reports inherited incompleteness and does not claim a complete family total

#### Scenario: Finding remains sound under omission
- **WHEN** a promoted finding cites a visible positive witness and its claim does not depend on absent rows
- **THEN** Ladon may retain the finding while labeling its witness scope and inherited collection coverage

### Requirement: Existing owner and compatibility preservation
Coverage, snapshot, and rendering integrity SHALL compose the existing public
CLI execution, report-version, canonical-payload, actionable-finding, atlas, and
proof-authority contracts. The capability MUST NOT introduce a parallel report
schema family, atlas engine, cache, or proof-xray authority. Additive report
fields and any incompatible serialization change MUST follow the existing
version and reader-dispatch migration contract.

#### Scenario: Existing reader lacks additive integrity fields
- **WHEN** a supported compatibility reader consumes a report produced during the documented transition
- **THEN** version dispatch preserves the reader contract and does not silently reinterpret missing coverage as complete

#### Scenario: Proof-shape evidence is absent
- **WHEN** a review region or atlas query lacks elaborated proof-shape evidence
- **THEN** coverage metadata reports that authority as unavailable and does not substitute lexical tactic counts as proof-xray results

### Requirement: Portable coverage and snapshot acceptance
Required acceptance gates SHALL use tracked, target-neutral fixtures and an
installed Ladon candidate. They MUST cover complete, empty, intentionally
projected, upstream-incomplete, and unknown-total collections; stratified
selection; severity accounting; incomplete atlas inputs; compatible and
incompatible fingerprints; one-analysis multi-format parity; deterministic
source-drift and mixed-read injection; pre-analysis multi-output rejection;
review regions; normalized determinism; and clean stdout/stderr behavior. A
mutable sibling repository MUST NOT define required counts, thresholds, or pass
criteria.

#### Scenario: Installed portable integrity matrix
- **WHEN** the required coverage and snapshot matrix runs from an installed candidate against tracked fixtures
- **THEN** all coverage, atlas, multi-format, drift, region-routing, output-channel, and determinism predicates pass without reading Matrix-Factorization

#### Scenario: Portable unindexable source
- **WHEN** a tracked portable case deterministically makes one in-scope source unit unindexable
- **THEN** the installed gate observes unknown total and omitted values, a truthful observed lower bound, incomplete authority, and no repository-wide absence or exhaustive query claim

#### Scenario: Optional live repository observation
- **WHEN** maintainers repeat the ordinary CLI analysis on an available Matrix-Factorization checkout
- **THEN** they record source and analysis fingerprints, dirty/drift state, coverage, output identities, hashes, timings, and peak RSS as observational evidence without changing portable gates
