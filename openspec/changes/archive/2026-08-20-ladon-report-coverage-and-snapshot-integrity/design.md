## Context

Ladon already has owners for bounded source indexing, typed v2/v3 reports,
process and output behavior, installed report-set/atlas workflows, and review
regions. The integrity gap is between those owners: canonical collections can
be capped before projection without a compositional coverage record, review
projection applies generic first-N limits, atlas consumers infer totals from
visible rows, and separate ordinary CLI invocations are needed for canonical
text and JSON outputs.

A large-repository trial made the failure modes concrete. A v3 `full` projection
declared no projection omissions even though its lexical declaration summary had
already omitted most candidates; review projection retained no command rows from
a present audit population; compact text foregrounded informational findings
while most errors were accounted elsewhere or omitted; and separate format runs
observed different source fingerprints during active edits.

This child composes these existing owners:

- `ladon-large-inventory-scale-contract` owns the source index and bounded
  canonical populations;
- `ladon-report-contract-v2` owns report versions, canonical payloads,
  projection compatibility, and render parity;
- `ladon-cli-execution-contract` owns syntax, process, exit, stream, stdout, and
  output-write behavior;
- `ladon-installed-reportset-workflow` owns atlas ingestion and query
  algorithms;
- `ladon-review-regions` owns review-region synthesis;
- `ladon-actionable-findings-workflow` owns finding evidence references and
  ordinary inspection actions; and
- `ladon-proof-xray-roadmap` remains the owner of future elaborated proof-shape
  authority.

The umbrella dependency graph requires two internal milestones so the coverage
foundation can be used by later producers without making their final review
integration a prerequisite of that same foundation:

| Milestone | Starts | Delivers | Dependency effect |
| --- | --- | --- | --- |
| `coverage-foundation` | immediately | collection coverage model, upstream-omission propagation, registration API, and generic snapshot identity | enables scope/join, declaration/audit, generated-family, and inspection children |
| `snapshot-and-region-integration` | after those four producer children | producer-aware stratification, atlas and inspection actions, final drift verification, one-analysis multi-format output, and integrity review regions | closes this child and the umbrella integration seam |

Text-backed evidence remains lexical or Ladon-derived navigation evidence. No
coverage state upgrades it to Lean elaboration, theorem truth, proof success, or
proof-shape authority.

## Goals / Non-Goals

**Goals:**

- Give every bounded collection a compositional, authority-scoped coverage
  record, including honest unknown-total states.
- Distinguish upstream analysis loss from intentional projection loss.
- Preserve every registered evidence stratum deterministically in review
  projection and account for every selected finding in compact text.
- Make atlas query exhaustiveness depend on compatible, sufficient source
  coverage.
- Establish one source snapshot identity per analysis, detect post-read drift,
  and render all requested formats from the resulting immutable decision.
- Route producer evidence through bounded canonical references and ordinary
  inspection actions.
- Gate both milestones with portable, installed, deterministic, and
  large-inventory predicates.

**Non-Goals:**

- No parallel report schema family, source-index/cache, CLI executor, atlas
  engine, review-region engine, or proof-xray authority.
- No multiple stdout documents, renderer-triggered analysis, or hidden
  caller-specific interface.
- No inference that omitted evidence is absent, that an observed lower bound is
  the repository total, or that lexical proof syntax is elaborated proof shape.
- No Matrix-Factorization paths, counts, thresholds, or mutable sibling checkout
  in required gates.

## Decisions

### 1. Deliver one capability through two dependency-safe milestones

`coverage-foundation` establishes types and registration contracts before any
new producer collection is implemented. The four producer children register
their canonical collections, strata, authority, and inspection identities
against that foundation. Their exit contracts stop at those producer rows and
ordinary action templates; they do not require or emit complete review-region
objects.

`snapshot-and-region-integration` begins only after those producer surfaces are
available. It wires their real strata into review projection, their collection
requirements into atlas queries, their ordinary actions into regions, and all
registered source-reading phases into final snapshot verification. All tasks
remain in this standalone packet, but apply must stop at the explicit Milestone
A exit gate until the producer packets are present.

Alternative considered: complete the entire report child first. That would
either hard-code future producer shapes or force producer children to replace
the just-built stratification and region logic, creating a dependency cycle in
practice.

### 2. Use a typed coverage envelope with an explicit unknown-total state

A shared coverage module will define one normalized collection record:

- stable collection identity and canonical JSON pointer;
- `visible`, the rows present in the current surface;
- `observedLowerBound`, the number of distinct matching rows actually observed
  before the current projection;
- `totalKnown`;
- nullable `total` and `omitted`;
- `completeness` (`complete`, `partial`, `unavailable`, or `unstable`);
- population, scope, authority, source/scope/analysis fingerprints; and
- typed causes identifying extraction, analysis, projection, drift, or
  compatibility loss and any controlling cap.

When `totalKnown=true`, invariants require
`total >= observedLowerBound >= visible` and `omitted = total - visible`. A
complete empty collection is therefore explicitly known as zero. When a source
unit cannot be indexed or an upstream phase cannot determine its population,
`totalKnown=false`, `total=null`, and `omitted=null`; only the observed lower
bound is reported. Such a row cannot be complete, and consumers must not replace
the unknown total with the observed count.

Alternative considered: use `omitted=0` whenever no cap supplied a count. That
turns ignorance into completeness and makes an unindexable file
indistinguishable from an empty one.

### 3. Register coverage once and derive it compositionally

The typed ReportV2 boundary will carry one canonical coverage registry keyed by
stable collection ID. Phase owners register their collections through a small
generic API rather than embedding incompatible count spellings in each section.
Collection rows, findings, summaries, regions, and atlas records retain
`coverageRef` pointers instead of copying registry payloads.

A pure derivation function composes coverage:

- projection decreases `visible`, preserves the known or unknown upstream
  population, and appends an intentional-projection cause;
- an upstream cap remains visible in `full` projection because full means only
  “no additional projection omission”;
- derived evidence inherits every source coverage reference and the weakest
  required authority;
- a subset-safe positive witness can survive partial input with an explicit
  scope, while an absence or exhaustive aggregate becomes unavailable; and
- incompatible fingerprints cannot be composed.

The foundation migrates all currently bounded canonical collections before its
exit gate. Later children register new collections through the same API. Legacy
readers that lack coverage fields treat completeness as unknown, never complete.

Alternative considered: recursively infer coverage from serialized list lengths.
That cannot recover pre-projection omissions or unknown source populations and
repeats the current bug.

### 4. Treat projection as policy over registered collections

V3 projection will operate on registered collection identities rather than
recursively taking the first N values from arbitrary mappings. Its omission
ledger references derived coverage rows and distinguishes upstream causes from
the projection's own selection.

In Milestone B, review projection uses a finite registered stratum key containing
evidence kind, severity, status, population, and command/module role. Each
present stratum receives a deterministic bounded allowance before stable
tie-breaking. The bound is per registered stratum, so every non-empty stratum
retains representation while the finite registry keeps total output bounded.
Equivalent insertion-order changes produce identical membership and bytes.

Summary projection may omit all member rows, but it still exposes coverage and
inspection routing. Full projection introduces no projection omissions and
retains all canonical rows that survived upstream analysis.

Alternative considered: reserve a few global slots for special cases such as
audits. That creates a growing target-specific exception list and still lets a
new evidence class disappear.

### 5. Reconcile compact text through the same selection ledger

Findings and region renderers will consume a shared text-selection ledger rather
than independently slicing rows. Findings are ordered by the established
severity order, then stable identity. For every selected finding the ledger
records one disposition: displayed in the primary list, rendered in a named
secondary section, or omitted with count, coverage, and ordinary inspection
route.

Text headers expose analysis/source identity and collection coverage relevant to
their compact claims. Structured and text outputs are tested for equal semantic,
severity, authority, and completeness counts.

Alternative considered: add a warning below the current informational sample.
That does not account for errors rendered elsewhere and cannot be mechanically
reconciled with JSON.

### 6. Make atlas requirements declarative and coverage-aware

The existing atlas reader and SQLite schema will import collection coverage,
population, scope, authority, and analysis/source fingerprints. Each existing
canned query registers the source collections it requires and whether its
meaning is exhaustive or subset-safe.

An exhaustive query is unavailable when any required collection has unknown or
incomplete population coverage, unless a query-specific proof establishes that
omission cannot change the result. Subset-safe queries return a result envelope
with inherited coverage and a nonclaim of exhaustiveness. Empty visible rows
from partial input never mean repository-wide absence. Report tables whose
identities cannot belong to one compatible snapshot are rejected or isolated by
the existing workflow rather than merged.

Alternative considered: show a generic “partial atlas” banner. Query meanings
depend on different source tables, so only per-query requirements can determine
whether a result remains sound.

### 7. Establish snapshot identity early and verify it after all source reads

Milestone A adds a snapshot registry and immutable identity without yet assuming
the final producer set. Every source-reading phase registers the inputs that
affect its output: the source-index manifest, Lean and layout files, configured
policies, explicit evidence inputs, and other content-addressed analysis
configuration. All analysis byte readers validate the bytes they actually
consume against that one captured manifest/index identity; a phase cannot
silently analyze a second version and still share the original snapshot
identity. Dirty Git state is optional observation and is not part of
byte-stability.

Milestone B performs final repository verification after the last registered
source-reading phase. It recomputes the same manifests, including discovery
needed to detect added or removed source files. A per-read mismatch or final
comparison change produces one structured
`source_changed_during_analysis` decision listing affected collection
registrations. Those coverages become `unstable` or partial, and the report
cannot claim a stable complete snapshot. Byte-stable dirty trees remain valid.

The snapshot decision is finalized before failure policy and serialization. A
deterministic injectable verifier seam supports drift tests without sleeps,
signals, or a private CLI mode; installed library gates exercise the same
production pipeline with a controlled mutation callback. A mixed-read fixture
changes a registered source between two readers and may restore it before the
final comparison; the second reader's attempted bytes fail the
captured-manifest check before they are accepted into analysis. Ladon does not
claim to detect an arbitrary change-and-revert event that occurs wholly between
registered reads and leaves every analyzed byte set and the final comparison
unchanged.

Alternative considered: compare Git revision/status before and after. Already
dirty files can change without changing either identity, and untracked or
configuration inputs may not be represented.

### 8. Render multiple formats from one frozen analysis artifact

After final snapshot verification the pipeline freezes one analysis artifact
containing ReportV2, analysis fingerprint, source snapshot identity, drift
decision, and coverage registry. All renderers consume that artifact and may not
invoke discovery, extraction, or Lean.

The CLI execution owner gains an additive repeatable
`--emit FORMAT=PATH` spelling for multi-file output while retaining the current
single `--format`/`--output` path. Destinations and duplicate formats/paths are
validated before analysis. At most one target may use `-`, so stdout still
contains one report document while other targets, if any, are regular files.
The repeatable canonical option cannot be mixed with the single canonical pair
or legacy `--json`/`--text` flags, and legacy/canonical mixing remains an
invocation error. All such conflicts fail before discovery or analysis. Legacy
multi-file flags continue only through their documented compatibility window.

Each destination is written atomically. A write failure follows the existing
output failure/exit contract, retains already committed outputs, reports the
failed destination on stderr, and never reruns analysis. Text and JSON carry the
same analysis and source identities, drift state, semantic counts, authority,
and coverage.

Alternative considered: internally invoke Ladon once per format. That recreates
the source-drift race and repeats expensive or stateful analysis phases.

### 9. Extend the existing review-region engine through a registry

Milestone A defines the generic registration shape but does not fabricate
producer rows. In Milestone B the existing review-region module registers
structurally joined architecture evidence, declaration collisions, audit
surfaces, generated-looking family candidates, and option/resource pressure.

A region contains bounded canonical references, a coverage reference,
authority/nonclaims, and a structured action from the ordinary inspection
surface. It does not duplicate source rows. A complete-empty producer may yield
explicit empty routing metadata; unavailable or unsupported evidence is not
replaced with an unrelated region.

Alternative considered: let every producer emit its own complete region object.
That duplicates projection, action, coverage, and rendering policy across
capabilities.

### 10. Make portable and installed predicates the release authority

Tracked fixtures cover complete, complete-empty, projected, upstream-capped,
unknown-total/unindexable, and unstable populations; all registered strata;
mixed finding severities; compatible and incompatible atlas fingerprints;
multi-format parity; deterministic drift injection; and region actions.

Milestone A has a focused schema/coverage/registration gate that producer
children can rely on. Milestone B runs the installed candidate, report/atlas/CLI
contracts, normalized determinism, source-drift injection, and the existing
portable large-inventory scale gate with explicit runtime, memory, and report
size budgets. A live Matrix-Factorization run remains optional observational
evidence.

## Risks / Trade-offs

- **[Risk] Coverage metadata materially increases report size.**
  → Store canonical coverage once in a registry and reference it; measure the
  installed large-inventory artifact and keep projection rows compact.
- **[Risk] Existing readers interpret absent coverage as complete.**
  → Version-dispatch legacy input to unknown coverage and add compatibility
  fixtures before emitting new fields by default.
- **[Risk] A per-stratum allowance grows with registered strata.**
  → Keep the stratum vocabulary finite and owned, expose its computed bound, and
  enforce installed report-size budgets.
- **[Risk] Per-read validation and final fingerprinting add large-repository I/O.**
  → Reuse source-index manifests and content metadata, rehash only registered
  components needed to verify stability, and enforce a scale budget.
- **[Risk] Milestone B can accidentally leak into producer implementation.**
  → Gate Milestone A independently, leave all producer-specific registration
  tasks explicitly blocked until their packets land, and keep this child as the
  sole integration owner.
- **[Risk] A partial output set remains after one file write fails.**
  → Preflight every destination, write atomically, identify committed and failed
  destinations in the operational diagnostic, and never imply transactional
  all-or-nothing output.

## Migration Plan

1. Implement and gate `coverage-foundation`: coverage types/invariants,
   canonical registry, upstream omission and unknown-total propagation,
   compatibility defaults, projection integration, and generic snapshot/region
   registration identities.
2. Publish the Milestone A exit contract for the four producer packets. Stop this
   packet's apply loop at that checkpoint until their canonical rows,
   authorities, strata, and ordinary inspection actions are available.
3. Apply and close the scope/join, declaration/audit, generated-family, and
   inspection producer children against the foundation; their region-facing
   deliverables are canonical registration rows and action templates only.
4. Resume `snapshot-and-region-integration`: finish producer-aware
   stratification, severity accounting, atlas requirements, per-read snapshot
   checks plus final drift verification, repeatable multi-format output, and
   registered review regions.
5. Update v2/v3 schemas/readers, installed CLI/report-set contracts, calibration
   artifacts, documentation, and release gates in the existing owner modules.
6. Run focused tests, the full suite, strict Python quality, package build,
   installed distribution matrix, large-inventory scale gate, normalized
   determinism, and strict OpenSpec validation.

Rollback must revert each milestone and its reader/schema changes together.
Milestone A remains a valid checkpoint while producer packets are in flight;
Milestone B must not be partially enabled with unregistered producer surfaces.

## Open Questions

None are blocking. The exact finite stratum vocabulary and collection IDs will be
recorded with their producer registrations during Milestone B; their coverage
semantics, authority rules, and dependency order are fixed here.
