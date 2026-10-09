# Proposal

## Why

The October follow-up in `FIRST-HAND-REPORT.md` records useful declarations being missed or replaced by unrelated lexical matches while a shared repository changes. Rebuilding private 775 MB indexes took about 93 seconds and contributed to an 18 GB index directory; the caller needs visible search limitations, an affordable update path and safe lifecycle management.

## What Changes

- Make exact-name misses and unverified/stale search results prominent, with bounded added/changed/removed source evidence and explicit stored/current identity meanings.
- Add an explicit incremental lexical update operation that publishes a coherent generation atomically, preserves evidence boundaries and reports when a full rebuild is required.
- Add index inventory and preview-first cleanup for disposable private generations, protecting active publishers, the default index and retained evidence.
- Make ordinary text status compact while preserving machine fields and an explicit detailed inventory.
- Reconcile the older report findings with their existing owners and current tests. Fix reproduced residuals through those owners rather than repeating already implemented work.

This umbrella has three ordered implementation packages: freshness/search diagnostics, incremental update, and index lifecycle. Its specifications and tasks are directly applicable; separate child scaffolding is unnecessary. Success is a caller finding a newly added declaration through an explicit update, understanding any remaining staleness, and reclaiming only explicitly selected disposable indexes. The real project is a read-only observation source; portable copies exercise mutations.

## Capabilities

### New Capabilities

- `ladon-index-freshness-diagnostics`: source deltas, exact/fallback match presentation, identity explanations and concise operational status.
- `ladon-incremental-lexical-index`: explicit incremental publication with full-build equivalence and concurrent-edit handling.
- `ladon-index-lifecycle`: bounded inventory, retention and ownership-safe cleanup of disposable local index files.

These names are absent from canonical specs. Archived name/freshness contracts and active hardening children remain authoritative for their existing behavior; this change adds the active-editing contract and references their residual work.

### Modified Capabilities

None. Existing pipeline compatibility and evidence-backed OpenSpec reconciliation requirements continue to apply.

## Impact

The main owners are `proof_search_index.py`, `proof_search_query.py`, `proof_search_cli.py`, source inventory/extraction, SQLite schema/publication and storage accounting. New CLI operations and additive diagnostic fields need installed-command, schema and compatibility coverage. Documentation and the maintained Ladon skills will describe shared-reader reuse, explicit update and safe cleanup. No model, Lean build, automatic repository edit or automatic deletion is required for lexical operations.

The report's timings, sizes and historical defects are attributed observations, not newly reproduced measurements. `sources.md` records current source findings, existing owners and the frozen report digest. New ranking engines, semantic extraction, database splitting and lineage deduplication remain outside this package unless a reproduced residual requires a separately scoped decision.
