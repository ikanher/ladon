# Proposal

## Why

Backward proof audits need to distinguish historical mathematical ideas from the dates of their Lean implementations. Ladon currently has no enforced historical attribution model, and a metadata-only upgrade must not discard or falsely refresh existing proof evidence.

## What Changes

- Add normalized, source-backed ideas, competing date attributions, persistent declaration links and an acyclic historical prerequisite graph.
- Expose exact years, explicitly estimated decades and unassessed dates without inventing historical priority or proof authority.
- Add a dedicated atomic v6-to-v7 migration with content-preservation metrics, separate from lexical refresh. Preserve the existing proof-input identity scheme for this additive metadata extension.
- Make authored `ladon-ideas.json` records reproducible across rebuilds; resolve declaration links against exact names and statement fingerprints, retaining stale/unresolved links.
- Supply public migration, synchronization and inspection commands, query projections, tests and measured evidence. No Lean build or shared live database replacement is needed for qualification.

Success means zero protected-data, association and query losses on fixtures and retained real-index copies, with adversarial controls showing the metric detects damage. Any unresolved preservation failure blocks rollout; revert only this change if it cannot be repaired.

## Capabilities

### New Capabilities

- `historical-idea-index`: Source-backed historical attribution, declaration correspondence and historical DAG navigation.
- `index-migration-preservation`: Measured, atomic additive index migrations with retained evidence and explicit rollback boundaries.

### Modified Capabilities

None. Existing `ladon-pipeline` extraction and proof-authority requirements remain unchanged.

## Impact

SQLite schema/layout validation, index lifecycle, name/type/lineage read projections and CLI documentation. No dependency upgrade, theorem implementation, automatic dating model or automatic Lean execution. Historical metadata does not become a proof dependency. The existing untracked files `100000-node` and `8` are outside this change.
