## Context

The lineage schema supplies closure-local nodes and indexed edges oriented from each
declaration to its dependencies. User-facing ancestry runs in the reverse direction,
from trust or selected boundary roots toward the target theorem.

## Goals / Non-Goals

**Goals:** deterministic parameterized SQL for closure lookup, reachability, minimum
depth, bounded representative routes, counts, and source joins, with explicit
freshness and cap semantics.

**Non-Goals:** no arbitrary SQL interface, no exhaustive simple-path enumeration,
no Python fallback for routine traversal, and no query across incompatible closures.

## Decisions

### 1. Resolve exactly one active fresh closure

Lookup uses the fully qualified theorem name plus current repository, schema,
source/configuration, toolchain, and helper identities. Ambiguous, stale, partial,
or absent rows produce distinct unavailable reasons before traversal starts.

### 2. Use recursive CTEs with cycle guards

Recursive queries carry closure id, node, depth, predecessor, edge kind, and a
delimiter-safe visited representation. They stop at `max_depth` and an internal
row ceiling. SCC membership is available for condensation when cyclic fixtures
would otherwise revisit nodes.

### 3. Separate reachability from route materialization

First compute reachable nodes and minimum depth using SQL aggregation. Then select
at most `max_routes` deterministic predecessor chains ordered by root kind/name,
distance, edge-kind sequence, and node name. This avoids enumerating every path.
Counts describe selected rows and known lower bounds; they do not claim total simple
path counts when enumeration was capped.

### 4. Keep filters in SQL

Edge-kind (`value`, `type`, `all`), root boundary (`trust`, `project`, `external`,
`package`, explicit declaration), generated inclusion, owner module/package, and
direction predicates are parameters in the query plan. SQL joins declaration rows
for source locations when available.

### 5. Treat query plans as tested behavior

Tests run `EXPLAIN QUERY PLAN` on representative forward, reverse, trust-root, and
source-join queries and require named indexes. Latency tests distinguish SQLite
execution from Python/CLI startup.

## Risks / Trade-offs

- [Visited-path strings consume memory] → Condense SCCs where needed, keep strict
  row/depth caps, and use them only during bounded route reconstruction.
- [Recursive CTE planner changes across SQLite versions] → Test semantic results
  portably and access paths on supported runtime versions without pinning opaque
  numeric plan costs.
- [Shortest paths hide longer meaningful branches] → Return branch counts and allow
  bounded alternate representatives without claiming completeness.
- [Empty rows are mistaken for no dependency] → Return closure/freshness/coverage
  state and omission reasons alongside every result.

## Migration Plan

Land the query service behind unit tests before CLI exposure. It reads only the new
schema and fails with a schema-generation diagnostic against v1. Rollback leaves
stored rows unused but intact until the disposable DB is rebuilt.

## Open Questions

- Whether a later SQLite version's built-in JSON aggregates materially improve
  route reconstruction enough to remove the small row-assembly layer.
