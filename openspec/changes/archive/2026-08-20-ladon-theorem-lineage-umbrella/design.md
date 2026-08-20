## Context

The theorem-capsule planner resolves a fully qualified theorem in the pinned Lean
environment and emits an unbounded complete semantic graph. Its edges point from a
declaration to its type or value dependencies. The proof-search index already owns
repository-local SQLite lifecycle, identity, integrity, and forward/reverse edge
indexes, but v1 does not ingest the theorem planner's exact dependency stream.

The Quux CDC example demonstrates the scale: 1,252 nodes, 60,409 edges, and 44,170
external-frontier edges. Enumerating every unfolded path is neither useful nor safe.
The product needs database-backed, bounded views over the actual compiled proof DAG.

## Goals / Non-Goals

**Goals:**

- Accept one fully qualified theorem name and return source-linked ancestry from
  declared trust roots or selected boundaries to that theorem.
- Store exact closure evidence once and answer repeated traversal through SQLite.
- Make actual-proof dependencies, representative paths, and mandatory bottlenecks
  distinguishable in every output.
- Give coders five linear, independently testable implementation packets.

**Non-Goals:**

- No enumeration of all possible alternative proofs.
- No lexical or parser edge promoted to Lean-authoritative lineage.
- No graph database, daemon, language server, or caller-specific command.
- No unbounded path expansion or claim that a displayed tree is the unique proof.

## Decisions

### 1. Land five packets in a strict database-first order

```text
theorem plan authority
        |
        v
DB schema + ingestion -> SQL queries -> projections/bottlenecks
                                           |
                                           v
                                    CLI + renderers
                                           |
                                           v
                              integration + calibration
```

Each child starts only after the prior child's portable exit class passes. This
avoids building renderers around an in-memory graph that the DB later replaces.

### 2. Extend the existing project-local database

Lineage uses `<repo>/.ladon/index/proof-search.sqlite` and its `--index` override.
The schema remains private. A schema-generation bump triggers a transactional
rebuild because the index is disposable generated state. Dedicated normalized
closure, node, edge, SCC, trust, and omission tables keep multiple theorem closures
and their provenance separate.

Alternative: store a second lineage SQLite file. Rejected because declaration
identity, project ownership, status, and lifecycle would be duplicated.

### 3. Ingest the theorem planner; do not invent a second extractor

Only a complete compatible `semanticGraph` with `lean_environment` authority can
be ingested as actual lineage. The adapter recomputes fingerprints, materializes
external frontier endpoints as typed nodes, validates every edge endpoint, and
publishes in one transaction. Capsule eligibility is recorded separately because
a complete semantic graph can remain useful even when a build-packaging facet is
unsupported.

### 4. Prefer SQL for graph work

Parameterized recursive CTEs own reachability, direction reversal, edge/boundary
filters, minimum depth, bounded route candidates, counts, and source joins. Required
indexes and `EXPLAIN QUERY PLAN` fixtures prevent accidental table scans.

Pure Python is allowed only after SQL returns a bounded subgraph and only where the
operation is materially clearer or more reliable outside SQLite: deterministic
dominators and reference-preserving tree unfolding. Those algorithms receive hard
node/edge limits and never query the repository themselves.

### 5. Return projections, not an exponential list of paths

The canonical result contains the selected subgraph plus representative shortest
spines, boundary summaries, repeated-node references, and optional bottlenecks.
Every cap reports truncation and omitted counts/reasons. `routes` means paths in the
actual compiled dependency graph; it never means alternative proofs.

### 6. Keep refresh behavior visible

The CLI first queries a fresh stored closure. A missing or stale closure does not
silently become lexical evidence. The user can request a supervised theorem-plan
refresh through the lineage command; progress and diagnostics remain on stderr.
The refreshed plan is validated and ingested before the SQL query runs.

## Risks / Trade-offs

- [Recursive SQL creates path explosion] → Select reachability/minimum-depth layers
  first, cap route candidates, and never promise exhaustive path enumeration.
- [Base-index rebuild discards stored closures] → Make regeneration explicit and
  cheap relative to the original plan; preserve only fingerprint-identical closures
  if safe copying is implemented.
- [Trust roots are confused with mathematical axioms] → Preserve Lean's exact
  declared-axiom kinds/scopes and state the trust-boundary nonclaim.
- [Collapsed views hide meaningful dependencies] → Keep full selected nodes/edges
  in JSON where within caps and list every collapse/omission reason.
- [Pure algorithms recreate the database graph] → Require bounded SQL inputs and
  unit tests proving no repository/database access in algorithm modules.

## Migration Plan

1. Bump the private proof-search schema generation and rebuild disposable indexes.
2. Add exact plan ingestion and validate integrity/index definitions.
3. Land SQL queries, then bounded projections, then the installed CLI.
4. Rebuild the Ladon, Quux, and Matrix-Factorization indexes; ingest selected
   theorem plans and record fingerprints/timings outside correctness fixtures.
5. Roll back by removing the generated DB and using existing `ladon theorem plan`;
   theorem capsule behavior remains compatible.

## Open Questions

- Whether a future version should retain fingerprint-identical lineage closures
  across an otherwise identical base-index rebuild.
- Whether DOT should be added later as an artifact renderer after text/JSON usage is
  calibrated; it is not needed for the initial command contract.
