# Proposal

## Why

Proof iteration makes lexical search stale, but Ladon currently refuses incremental updates when the same database retains semantic, lineage or ProofIR evidence. Adam field feedback R02 demonstrates this obstacle; users should be able to refresh search without discarding evidence or associating an old proof with new source bytes.

## What Changes

- Extend explicit `proof-search index update` to preserve supported evidence-bearing bases as immutable, identified SQLite snapshots before publishing refreshed lexical data at the same index path.
- Add bounded history inventory and explicit historical lineage inspection. Current search uses current declarations; historical records retain their original subjects, environments, coverage and outcomes.
- Keep lexical freshness, historical evidence availability and current compiled association separate in text and JSON. A lexical update neither builds Lean nor renews checking evidence.
- Extend publication, compatibility and cleanup handling for the snapshot lifecycle, including source-change diagnostics with bounded path details and retry guidance.
- Deliver through recorded red/green/refactor cycles, public CLI acceptance tests, crash/concurrency controls, installed contracts and a disposable real-project exercise. Success means edited declarations are searchable and original evidence remains inspectable without false current associations.
- **BREAKING (private storage only):** version the active database/history layout so unsupported readers reject it. Preserve public command spelling and existing evidence schemas; identify any unavoidable public output version changes before implementation.

Automatic refresh/watchers, per-theorem proof reuse across source generations, history deletion, and new proof/search engines are deferred. Historical snapshots remain protected from existing prune. The first release reports disk costs and refuses publication on storage failure without deleting history.

## Capabilities

### New Capabilities

- `ladon-index-evidence-history`: Retained generation identity, evidence-preserving lexical update, historical read selection, atomic publication and protected lifecycle. Requirements are in `specs/ladon-index-evidence-history/spec.md`.

### Modified Capabilities

None in the synchronized main specs. The completed, unarchived `ladon-active-project-index-umbrella` already permits preserving original evidence or refusing unsupported updates. This change strengthens supported cases to preservation while keeping unknown formats fail-closed; it does not rewrite historical acceptance records. Existing ProofIR identity and authority requirements remain unchanged.

## Impact

- Owners: `proof_search_index_update.py`, `proof_search_retained.py`, `proof_search_schema.py`, index CLI/status/lifecycle, SQLite publication, lineage read selection and mutation entrypoints. Semantic and ProofIR readers/writers need compatibility checks; their evidence validators remain authoritative.
- Tests: active index, lifecycle, publication, lineage, semantic and ProofIR contracts, plus installed CLI scenarios on supported Python runtimes.
- Documentation: CLI/index guidance and Ladon skill. Bump the package version after qualification; no mathematical project edits or builds are required for lexical maintenance.
- Sources: conversation design, retained R02 triage at `../ladon-proof-workflow-field-reliability/evidence/r01/FEEDBACK_R02_TRIAGE.md`, and `temp/ladon-adam-supported-bias-feedback-r03.zip` (diagnostic motivation; successful checking remains historical field evidence).
