## Why

Worker artifacts validate as a batch but cannot be incrementally projected or queried when derivations externally reference their check runs. Several query limits and result counters also permit misleading output.

## What Changes

- Resolve incremental references over existing database artifacts union the incoming atomic batch.
- Distinguish derivation-topology references from external evidence references.
- Freeze positive limits, accurate matched/returned/truncated accounting, set-oriented dossiers, and complete derivation-step rendering.

## Capabilities

### New Capabilities
- `proofir-v3-cross-artifact-resolution-and-query-contracts`

### Modified Capabilities

## Impact

Changes SQLite projection transactions, reference validation, graph navigation, proof slices, dossiers, query result schemas, and indexes/access-path gates.
