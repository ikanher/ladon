## Context

SQL can select exact reachable subgraphs and representative routes efficiently, but
the raw result is still too dense for review. Projections must preserve node sharing,
authority, and omissions while exposing understandable proof ancestry.

## Goals / Non-Goals

**Goals:** stable projection vocabulary, representative spines, boundary collapse,
branch summaries, mandatory bottlenecks, and bounded tree views.

**Non-Goals:** no exhaustive path list, aesthetic graph layout engine, mathematical
importance score, or claim that a shortest route is the proof's main idea.

## Decisions

### 1. Define render-neutral projection rows

All views return canonical nodes, edges, roots, routes, repeated references,
collapses, bottlenecks, bounds, and omissions. Text and JSON render the same model.
Source locations are optional with an explicit status.

### 2. Use SQL for projections that are relational

Boundary membership, owner/package grouping, generated-node filtering, edge-kind
selection, degrees, branch points, and representative shortest spines remain SQL
queries. Collapse rows list member counts and boundary identities so hidden detail is
auditable.

### 3. Use a pure algorithm only for dominators

Mandatory bottlenecks mean nodes present on every selected root-to-target route in
the bounded authoritative subgraph. Implement deterministic iterative dominators on
the SCC-condensed graph returned by SQL. The function accepts immutable node/edge
rows only, has no filesystem/SQLite access, and rejects inputs above explicit caps.

### 4. Unfold trees by reference, not duplication

Tree output follows deterministic selected edges toward the theorem. On second and
subsequent visits, emit a shared-node reference. Cycles emit SCC references. Depth,
children, nodes, and rendered bytes are independently capped and reported.

### 5. Preserve the actual-versus-possible distinction

Call rows `dependency routes`, `spines`, and `lineage`, never `proof alternatives`.
The nonclaim states that the graph describes dependencies of one compiled proof term
and does not enumerate other proofs Lean might accept.

## Risks / Trade-offs

- [Dominator result changes under filtering] → Record the exact edge kind, boundary,
  generated policy, and selected subgraph fingerprint with every bottleneck row.
- [Collapsing external nodes hides axioms] → Trust roots remain individually visible
  even when their owner package is collapsed.
- [Tree output implies uniqueness] → Mark shared references and label the view as an
  unfolding of a DAG.
- [Algorithm memory grows] → Require SQL caps before invocation and add worst-case
  diamond/chain fixtures.

## Migration Plan

Add projection models after SQL query stability. Keep raw bounded SQL rows available
for debugging until text/JSON parity passes. Removing this layer falls back to the
SQL result without changing stored evidence.

## Open Questions

- Whether users value immediate dominators only or the complete dominator chain;
  initially expose both in JSON and the immediate chain in text.
