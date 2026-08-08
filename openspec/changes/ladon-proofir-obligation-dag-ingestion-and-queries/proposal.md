## Why

ProofIR obligation DAGs encode conditional, checked, and Lean-backed routes that
are useful to reviewers, but they are currently isolated JSON artifacts. A
normalized SQL graph can answer bounded route questions while keeping those
edges rigorously separate from compiled theorem lineage.

## What Changes

- Normalize `proof_ir_v2_obligation_dag` imports, obligations, produced facts,
  statuses, authorities, caveats, and directed use/produce edges.
- Normalize the matching DAG check witness as a separate checking artifact,
  linked only when identity and content evidence agree.
- Add indexed forward/reverse reachability, shortest representative routes,
  status/authority boundary filters, and bounded recursive CTE queries.
- Detect missing endpoints, duplicate conflicts, cycles, stale check witnesses,
  and cap exhaustion without inventing proof conclusions.
- Preserve the nonclaim that ProofIR obligation routes are not Lean declaration
  dependencies or proof-term authority.

## Capabilities

### New Capabilities

- `ladon-proofir-obligation-dag-ingestion-and-queries`: Constrained persistence
  and SQL-first traversal of normalized ProofIR obligation evidence.

### Modified Capabilities

None.

## Impact

- Adds normalized ProofIR node/edge tables, indexes, integrity rules, and route
  result schemas.
- Adds recursive-SQL tests and frozen CDC, diamond, cycle, stale, and malformed
  fixtures.
