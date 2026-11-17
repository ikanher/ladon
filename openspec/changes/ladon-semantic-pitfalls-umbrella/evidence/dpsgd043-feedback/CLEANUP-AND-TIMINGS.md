# Catalog cleanup and update timing continuation

On 2026-11-17 the owner explicitly authorized wiping stale catalog entries.
A new public cleanup preview found 50 registered rows and zero existing archive
bytes. Public apply completed; a separate read confirms zero history rows and
unchanged active generation identity. No archive file or source file was deleted.
CATALOG-CLEANUP-RESULT.json records the bounded outcome. The full local preview
and receipt remain under .codex/state/dpsgd043-followup/.

Incremental updates now report exclusive `phaseSeconds` for enumeration, hashing,
extraction and database work, on both changed and no-op paths. Nested phase time
is subtracted from its parent. A deterministic clock test checks that accounting
and request isolation. Source stability captures remain in the hashing phase;
unchanged inputs report zero extraction. Uninstrumented orchestration, locking
and final atomic publication remain outside those phase totals and within the
existing elapsedSeconds. docs/CLI.md defines the scope; both skills link it.

The integrated archive/update/search suite passes 107 tests in 4.25 seconds.
The timing-only tests pass after a lint-only consolidation of nested context
managers. Repository Ruff, scoped strict quality and OpenSpec validation pass;
both skills validate. No full suite or new installed release qualification was
run, and the version remains 0.4.3. Changes are uncommitted.

V.2 is complete within this scope. V.1 remains open: the preferred next design
is bounded batch reads over one SQLite transaction, with source validation around
the batch, explicit observation-window authority and no agent-specific cache.
Cross-process tokens/watchers are not implemented. The old 75.7-second update
and historical large-capsule memory workload were not rerun.
