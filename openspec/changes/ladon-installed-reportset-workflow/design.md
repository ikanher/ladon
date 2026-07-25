## Context

Atlas, SQLite query, structural diff, reviewer-card, and workflow engines
already work as checkout scripts. This child packages those existing engines
behind supported installed Ladon operations and adds bundle ingestion.

## Decisions

### Install one coherent report-set surface

The ordinary `ladon` CLI exposes atlas, query, diff, cards, and workflow
operations using the same options and behavior for every caller. Checkout
scripts become thin wrappers over packaged functions during migration.

### Existing libraries remain authoritative

CLI handlers delegate directly to `ladon.atlas`, `ladon.atlas_sqlite`,
`ladon.atlas_diff`, and `ladon.atlas_workflow`. No second graph, query
evaluator, diff algorithm, card model, or priority calculation is created.

### Inputs validate before derivation

Readers accept supported canonical reports or versioned bundles, resolve
members relative to the bundle, and verify hashes and report versions.
Non-success entries remain workflow diagnostics. Atlas terminology separates
highlighted module nodes from total analyzed inventory modules.

### Semantic comparison remains external

Generic atlas diff compares existing structural rows only.
`ladon-theorem-surface-changelog` and the retained Review Radar roadmap remain
the sole semantic theorem-change owners.

## Risks

Source scripts and installed handlers can drift. Parity tests exercise both
against the same library. Unknown versions, missing members, and hash mismatch
fail before an apparently complete atlas is emitted.
