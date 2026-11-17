# Disposable current index and explicit legacy cleanup

Implemented 2026-11-17 after the owner rejected automatic snapshots. Ordinary
updates now invalidate supported derived semantic/lineage observations and report
`derivedEvidence`, `historyPolicy` and `historyIntegrity`. No persistent archive
is created or hashed. No-op updates retain existing observations and bytes.
Temporary publication candidates retain the existing atomic replacement and
cleanup behavior. Unsupported table layouts still reject update rather than
silently dropping unknown data.

Authored idea metadata is distinct from extracted semantic cache rows. The
updater retains the existing authored tables and source-catalogue reconciliation;
a dedicated test confirms database-authored ideas survive default updates.
Separately saved audit files are unaffected. Removed cached evidence becomes
unavailable until regenerated; it never inherits fresh authority by name.

The optional explicit `--archive-history` mode preserves old behavior. Prior
archive tests now request that mode. HISTORY-TEST-PRESERVATION.json confirms all
assertions in the ten edited existing test files are unchanged. New tests cover
the current-cache default independently. No new automatic evidence archive or
SQLite schema migration is introduced.

`index history-cleanup` previews selected registered IDs, catalog data, paths,
file identities and bytes. Apply requires the saved preview, validates ownership
and file state under the publication lock, commits catalog removal, then unlinks
only selected files. Partial unlink leaves an orphan that the same preview can
finish removing. Unknown files, replacements, symlinks and hardlinks are excluded
or rejected. Files already missing can be removed from the catalog explicitly.

A read-only MF preview found all 50 registered snapshot files absent and zero
existing bytes; the owner confirmed personally deleting the history directory.
This work did not remove those files or apply cleanup to the donor catalog.
The exact local preview is .codex/state/dpsgd043-followup/mf-history-cleanup-preview.json.

## Validation

The integrated archive/current-index suite passed 93 tests in 3.69 seconds:

```
.venv/bin/python -m pytest -q tests/test_disposable_index_history.py tests/test_disposable_history_cleanup.py tests/test_index_history*.py tests/test_proof_search_active_index.py tests/test_lexical_extractor_recovery.py tests/test_lexical_scope_recovery.py
```

Tests include changed/no-op inputs, derived evidence, authored ideas, explicit
saved outputs, missing historical files, unknown files, changed previews/files,
symlinks, interruption/retry, publication lock contention, source-change failure
and atomic-publication behavior. Repository Ruff and scoped strict complexity/
dead-code checks pass. Both skills validate; the umbrella validates strictly.
No full suite, installed release qualification or independent audit was repeated.
Changes remain uncommitted and the package version remains 0.4.3.

The delivered freshness observation does not implement shared validation tokens.
Incremental update enumeration/hashing/extraction/database timings also remain
open, as V.1/V.2 in tasks.md. Historical large-capsule memory work was not rerun.
