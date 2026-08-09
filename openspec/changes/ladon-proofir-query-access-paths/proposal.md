## Why

Several implemented dossier and triage queries scan whole ProofIR relations because their predicates do not match any index. Foreign-key constraints are present, but not every operational child lookup or cascade path is indexed.

## What Changes

- Inventory every production SQL predicate, join, ordering, and foreign-key child path.
- Add exact-name, attachment, diagnostic, obligation, replay, freshness, state, and other measured access paths.
- Prefer compact partial indexes for sparse negative-evidence triage.
- Add populated query-plan and bounded-latency tests rather than validating names alone.

## Capabilities

### New Capabilities

- `ladon-proofir-query-access-paths`: Explicit core and ProofIR lookup, triage, graph, and foreign-key child access paths validated on populated data.

### Modified Capabilities

## Impact

Changes private DDL, ProofIR queries, schema validation, catalog fixtures, and plan tests; ProofIR evidence remains quoted evidence.
