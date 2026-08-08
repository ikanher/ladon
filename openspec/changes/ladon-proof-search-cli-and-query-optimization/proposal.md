## Why

Proof-search startup and graph-backed queries currently pay avoidable import, duplicate traversal, and N+1 SQL costs that will obscure semantic-search latency.

## What Changes

- Add a lightweight installed entrypoint with lazy proof-search and ProofIR imports.
- Reuse one bounded lineage walk instead of acquiring it twice.
- Batch boundary metadata and ProofIR path nodes in set-oriented queries.
- Preserve existing result contracts, stream behavior, and exit codes.

## Capabilities

### New Capabilities

- `ladon-proof-search-cli-and-query-optimization`: Lower CLI startup and constant-query-count graph-backed materialization.

### Modified Capabilities

## Impact

Refactors entrypoint dispatch, proof-search imports, theorem-lineage queries, ProofIR route materialization, trace tests, and startup benchmarks.
