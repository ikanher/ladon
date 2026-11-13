# Design

## Context

See [proposal.md](proposal.md) and [the reproduction](evidence/README.md).
The Lean helper expands project-owned declarations and records external library
frontiers. Ingestion already stores complete typed edges in `lineage_edges` and
node identities in `lineage_nodes`, scoped by an exact closure ID.

The current `theorem_lineage_query._walk_rows` carries a path string in a
`UNION ALL` recursive query. Repeated visits through different paths consume the
internal 10,000-row ceiling. `theorem_lineage_projection.project_lineage` then
uses `_route_edges(routes)` even for graph view, so that view contains only edges
from the bounded representative routes. Its inherited `returned.edges` counts
route-edge occurrences, whereas the projected edge list contains distinct pairs.
Neither behavior is repaired by increasing the displayed node budget.

The current canonical spec inventory does not contain the old lineage capability
names. The archived SQL-query contract nevertheless explicitly forbids enumerating
all simple paths as an intermediate operation. Preserve that history; this new
cohesive capability restores the intended acquisition behavior. The active storage
budget/publication change remains independent and is not marked complete here.

## Goals / Non-Goals

**Goals:** A caller can retrieve an entire stored project closure, know precisely
which graph was selected, and request representative routes without path explosion.
Existing freshness/authority and publication protections remain authoritative.

**Non-goals:** Re-extracting every library proof, proving mathematical truth,
inferring historical influence from dependencies, accepting source-only graph
edges, fixing unrelated storage-publication interruption tests, or adding a GUI.
A missing/stale compiled closure remains an acquisition obligation, not something
a projection can manufacture.

## Decisions

### 1. Add a closure view instead of redefining graph

Add `closure` to the public view choices in `theorem_cli.py`. Its graph is the
stored closure selected by exact identity and explicit edge/generated filters.
The existing `graph` view remains a graph of representative routes. Changing
that meaning silently would change output size and invalidate existing clients.

Closure selection is independent of root-to-target route boundaries. The output
records `selection = whole-stored-closure`; `--root` and nondefault route-boundary
selectors are rejected with a targeted diagnostic. Route depth/route-count options
are reported inapplicable, never reported as graph completeness controls. Common
node, typed-edge and byte limits apply. Examples must not suggest that `--from
trust` expands external proofs to axioms.

Edge-kind filtering restricts edges. The selected node population is the stored
node population after the generated-node policy, including the target. Dropping
nodes drops incident edges, records the selection omission, and does not synthesize
shortcut edges. With no filters and sufficient caps, exact equality with stored
nodes and typed edges is the primary acceptance oracle.

### 2. Query the closure directly, with exact caps

Introduce a focused closure-query owner beside `theorem_lineage_query.py`. Reuse
`inspect_lineage_closure` and identity construction; do not duplicate freshness
logic or write a second evidence database. Select from one compatible closure in
a coherent read transaction. Use parameterized closure-scoped SQL, stable ordering,
and `LIMIT cap+1` or exact counts. Never expand paths for this operation.

Select the target first, then remaining nodes by canonical name. Return typed
edges only when both endpoints were selected; count cap-excluded edges separately
from filter exclusions. Query edge populations before display truncation so that
complete coverage can be distinguished from a well-formed partial graph. No
schema migration or Lean-helper change is needed for this slice.

The current projection algorithm cap (`5,000` nodes and four times that many edges)
protects tree/dominator operations. Do not apply that unrelated cap to streaming
or bounded serialization of a closure graph. The closure uses explicit node,
edge and byte limits and performs no tree unfolding or dominator computation.

### 3. Separate reachability from route construction

For route views, replace `_walk_rows`' path-expanded traversal with deterministic
frontier expansion over distinct declarations and minimum depths. Use existing
forward/reverse closure indexes. A visited set and predecessor data are bounded
by the declared distinct-node budget. Fetch indexed adjacency rows in bounded
batches, stop at a public work budget, and record any unexpanded frontier.

Introduce an explicit unique graph-work limit (proposed CLI name
`--max-traversal-edges`, default `100000`) instead of an invisible path-prefix
ceiling. Count examined typed adjacency rows; do not allow one extra path to
re-expand a visited declaration. This is a change of work unit, not a larger
allowance for the old exponential algorithm. Keep output-edge and route limits
separate. Probe an outgoing edge at the depth boundary before deciding whether
reachability was depth-truncated.

Construct a bounded deterministic set of representative shortest predecessor
chains only after reachability. Stable name/edge-kind tie-breaking is required.
Do not enumerate all simple paths or claim an exact total path count. Preserve
SCC identities; a cyclic component does not invalidate finite reachability.
Historical archived requirements that mention recursive SQL are implementation
precedent; indexed bounded frontier queries are chosen because they deduplicate
nodes without carrying exponentially many path strings.

### 4. Report separate coverage and count meanings

Add a versioned coverage object with these distinct parts:

- `sourceClosure`: recorded extraction status, closure identity, project/external
  boundary counts, and stored omissions.
- `selectedGraph`: selection/filter policy, selected and returned unique node and
  typed-edge counts, graph-cap omissions, and `complete/partial/not-assessed`.
- `representativeRoutes`: `not-requested`, `complete-for-declared-selection`,
  `partial`, or `not-assessed`, with its own cap and deterministic policy. This
  never means enumeration of all possible proof routes.
- `externalExpansion`: `project-owned-with-library-frontier` for the current
  extractor; no implication of transitive library expansion.

Keep the existing evidence receipt's authority and theorem-check nonclaims.
Row coverage is not permission to upgrade `analysisCompleteness`, environment
match, or execution binding. In particular, stored evidence remains a stored
observation even after a complete projection.

The closure's `returned.edges` counts typed edge records. For existing route-based
views add clearly named unique-pair and route-occurrence counts and reconcile the
legacy count documentation; do not leave a field ambiguously disagreeing with its
payload. Use a projection/coverage version when changing a count's meaning. Define
fingerprints over canonical selected nodes, typed edges, filters and coverage,
excluding elapsed time and unrelated database state.

### 5. Preserve history and read-only behavior

Wire the new view through both live and historical lineage entry points.
`--refresh never` must remain free of Lean/Lake execution and evidence mutations.
Historical selection retains historical source identity and explicitly lacks a
current compiled-environment assertion. Missing, ambiguous, stale or corrupt
selection fails closed before projection. A byte-limit or rendering error uses
the existing atomic-output path and leaves an existing output untouched.

### 6. Tests and metrics precede implementation

Use existing ingestion fixtures to build exact finite graphs; expected sets come
from fixture input, not from the new query. Cover a 20-layer diamond (many paths,
fewer than 100 nodes), disconnected excluded records, self-loops/SCCs, two edge
kinds per pair, hidden generated bridges, exactly-at-cap and cap-plus-one cases,
stale identities and historical snapshots. Include an adversarial depth-boundary
case even though a current test expects `truncated=false` for a bounded search:
that test must be split into exhausted-frontier and genuinely cut-off cases.

Acceptance metrics:

| Metric | Gate |
| --- | --- |
| Missing/extra selected node and typed-edge sets | Both empty when budgets suffice |
| False-complete results under caps, filters or stale evidence | Zero |
| Payload/count disagreement and dangling endpoints | Zero |
| Graph result changes caused solely by route-count limit | Zero for closure view |
| Reachability expansion | Each distinct node expanded at most once; examined typed adjacency bounded by declared work |
| Determinism | Canonical payload/fingerprint identical under insertion reordering |
| Warm stored query side effects | No Lean/Lake execution or evidence mutation |
| Existing lineage regression suites | Pass, with intentional coverage-semantic changes documented |

After synthetic gates pass, replay the retained gradient field case with the same
node/edge/byte limits. Exact node and typed-edge sets must match the selected stored
closure, not the old route graph. Preserve old failing evidence. Measure wall time,
peak process-tree RSS when available, and selected/output counts separately. Keep
any live acquisition at the existing 120-second, 8-GiB child limit and 1536-MiB
complete-database ceiling; a projection fix must not depend on raising them.

## Risks / Trade-offs

- **Large complete outputs** → Require finite budgets, cap+1 detection and atomic
  output; return honest partial coverage or a bounded output failure.
- **Semantic drift between graph and routes** → Add a new view, typed count/version
  fields and explicit compatibility tests rather than silently reinterpreting data.
- **Cycles and filtering create false paths** → Keep SCC evidence, preserve typed
  records, and never reconnect hidden nodes with invented compiled edges.
- **Independent reads observe different publications** → Select identity/counts/
  rows in one read transaction and bind the exact closure ID throughout.
- **A successful field run is mistaken for universal proof** → Finite fixtures test
  boundary semantics; the field run validates only its recorded closure and budgets.
- **Performance route fails its own work bounds** → First run the shared-diamond
  fixture with a small deterministic work budget. Stop and revise traversal if work
  grows with path count; do not tune the old recursion ceiling upward.

## Migration Plan

This is additive at the CLI and read-only with respect to existing closure data.
No database migration, re-ingestion or cache deletion is needed. Update help,
documentation and the maintained skill with the view distinction and completeness
semantics. Run focused query/projection/CLI/history tests, then the existing Python
quality gate and field replay. If release verification fails, revert the new query/
view wiring; existing stored closures and prior views remain available. Do not
rewrite or delete lineage evidence during rollback.

## Implemented follow-up: stored-query validation efficiency

This follow-up was prompted by an internal-use review on 2026-11-14. It preserves the completed projection contract and introduces no persistent
cache. The first-stage implementation and measurements are recorded in
[evidence/query-validation-review-r01/IMPLEMENTATION.md](evidence/query-validation-review-r01/IMPLEMENTATION.md).

The live CLI currently performs full status inspection (including dbstat storage
accounting), two repository captures for freshness/stability, and a third
capture for lineage identity before the selected-closure lookup. Historical
queries already select an archived identity and explicitly withhold current
association; reuse that authority distinction for any later snapshot API.

The first implementation should separate minimal compatible-index/closure lookup
from comprehensive status diagnostics. A missing closure under `--refresh never`
can be returned without source capture. Supported schema and layout checks remain
required; an incompatible or corrupt index must not be treated as an empty one.
For an existing live closure, strict validation must supply the same validated
snapshot used to construct the query identity. Preserve a defined stability
check; removing the third capture does not justify removing change detection.
Read metadata, evidence generation and closure/projection rows in a coherent
SQLite transaction. Keep publication and refresh policies unchanged.

Measure elapsed time, repository-capture counts, status/diagnostic work and closure
lookup separately for present and absent closures. Compare identical projections
and evidence receipts on unchanged sources; retain stale-source/configuration,
toolchain mismatch, unstable source, missing/corrupt index and output-cap cases.
Reduced elapsed time alone cannot establish freshness or mathematical authority.

Shared snapshot validation is a later contract decision: separate agent CLI
processes require cross-process coordination. A waiter may reuse an explicit
validated snapshot only with that snapshot's original scope. A token binds the
resolved repository/worktree, source/configuration/toolchain identities, index
instance and evidence generation, and relevant helper/schema versions; it does
not guarantee the filesystem stayed unchanged. Expiry, cancellation, validator
failure, index replacement and concurrent publication need bounded defined
behavior. A database read transaction alone does not freeze source files.

Persistent result caching follows only a measured residual need. Its identity
must include the selected closure/version, snapshot and index identity, all query
filters/projection limits and relevant output/schema/helper versions. Cache hits
must not upgrade evidence authority, freshness, coverage, or completion. Caller
labels serve accounting/cancellation rather than cache identity or trust. Time,
mtime or watchers alone cannot authorize a live-fresh claim. Prefer the existing
historical path when immutable archived evidence already answers the question.
