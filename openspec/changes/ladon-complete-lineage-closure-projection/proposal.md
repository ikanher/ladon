# Proposal

## Why

Ladon can successfully ingest a complete project-owned compiled dependency closure,
yet its graph projection is built from a bounded list of routes. In the reproduced
historical averaging case, a stored closure with 2,242 nodes and 47,533 typed edges
produces a truncated graph with 1,072 nodes and only 23 distinct edges despite large
node/edge budgets. Shared paths exhaust an internal 10,000-row expansion limit.
This prevents the user from obtaining a complete graph of evidence already stored.

## What Changes

- Add an explicit `theorem lineage --view closure` projection that reads the
  stored, typed dependency graph without enumerating paths. Preserve the existing
  route-oriented meaning of `--view graph` for compatibility.
- Replace path-expanded reachability in route acquisition with distinct-node,
  minimum-depth discovery followed by bounded representative-route construction.
- Report stored-closure coverage, selected-graph coverage, route coverage and
  external dependency boundaries separately. Exact counts and completeness must
  refer to the same selected population; never describe a bounded route sample as
  the entire dependency graph.
- Preserve freshness, source/toolchain identity, historical-observation authority,
  typed edges, SCCs, finite resource limits and failure behavior. A project-complete
  closure remains bounded at external library declarations.
- Supply deterministic diamond/cycle/filter/cap tests and a regression of the
  recorded field case. Success is exact stored-row coverage with sufficient
  declared graph budgets, independent of the number of possible paths.

See [the capability specification](specs/ladon-lineage-closure-projection/spec.md)
for acceptance requirements and [the field evidence](evidence/README.md) for the
observed behavior. This packet specifies implementation; it does not claim the
limitation is fixed.

## Capabilities

### New Capabilities

- `ladon-lineage-closure-projection`: Complete, resource-bounded projections of a
  stored compiled project closure, with independent reachability/route coverage.

### Modified Capabilities

None in the current canonical capability inventory. Archived lineage query and
projection contracts are explicit compatibility inputs; their prohibition on
intermediate enumeration of all simple paths is currently not met by the inspected
path-carrying recursive query. This change restores that behavior without rewriting
archived history or duplicating ProofIR derivation-hypergraph semantics.

## Impact

The relevant owners are `theorem_lineage_query.py`,
`theorem_lineage_projection.py`, `theorem_lineage_cli.py`, `theorem_cli.py`, and
historical lineage selection. Tests extend the existing lineage query, projection,
CLI, history and hardening suites. CLI documentation and the maintained Ladon skill
need matching usage/coverage guidance. The stored closure schema and Lean extractor
need no expansion for the initial implementation: the necessary rows already exist.
No automatic external-library recursion, source-proof inference, or new theorem
checking is included.
