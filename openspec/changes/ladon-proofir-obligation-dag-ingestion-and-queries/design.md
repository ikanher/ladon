## Context

The current Quux CDC `proof_ir_v2_obligation_dag` has imported facts,
obligations, produced facts, explicit authorities/statuses, and a conditional
global conclusion. SQLite recursive CTEs can already recover routes from paper
inputs or theorem hypotheses to the conclusion, but Ladon has no normalized
identity, integrity, freshness, or bounded result contract for this graph.

## Goals / Non-Goals

**Goals:**

- Persist admitted obligation DAGs and checker witnesses transactionally.
- Validate all fact/obligation endpoints and conflicting duplicates.
- Query bounded routes in either direction with SQL.
- Preserve status and authority changes on every route.

**Non-Goals:**

- No conversion of obligation edges into theorem-lineage dependencies.
- No claim that checker validation establishes mathematical truth.
- No exhaustive enumeration of all routes.
- No generic adapter for arbitrary objects containing `uses` and `produces`.

## Decisions

1. Add artifact-owned DAG, node, edge, authority, and omission tables. Normalize
   imported facts, obligations, and produced facts as typed nodes; represent
   use/produce relationships as directed edges with the obligation identity.
2. Validate uniqueness, endpoint closure, supported status/authority values,
   and deterministic ordering before inserting. Preserve unknown quoted values
   only through diagnostics rather than silently mapping them.
3. Treat check witnesses as separate artifacts related by explicit DAG ID and
   source artifact identity. `validated` means the named checker contract was
   reported, not that Ladon reran it or promoted its claims.
4. Use parameterized recursive CTEs for reachability, minimum depth, forward and
   reverse traversal, and representative paths. Apply node, edge, depth, route,
   and output-byte caps with explicit truncation.
5. Require forward `(dag_id, source, kind, target)` and reverse
   `(dag_id, target, kind, source)` indexes plus query-plan tests.
6. Cycles are retained and diagnosed. Traversal uses visited-node state and
   caps; it does not reject an otherwise inspectable artifact solely for being
   cyclic unless the dialect contract forbids the cycle.

## Risks / Trade-offs

- [Path counts grow exponentially] → Return selected subgraphs and bounded
  representative routes, never all paths.
- [Mixed authority is flattened] → Carry status/authority per obligation and
  summarize every transition in results.
- [Checker witness becomes a trust oracle] → Keep checker relation and quoted
  guarantee separate from DAG node status.
- [SQL traversal becomes opaque] → Add small chain, diamond, mixed-authority,
  and cycle fixtures with exact expected rows and query plans.

## Migration Plan

1. Freeze minimal and CDC-derived DAG fixtures.
2. Add failing normalization/integrity tests.
3. Add schema rows and transactional ingestion.
4. Add recursive SQL queries, caps, and result schemas.
5. Add checker-witness relations and negative stale tests.

## Open Questions

- None for v1; dominators and graph visualization remain future projections.
