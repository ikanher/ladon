# Internal consumer follow-up implementation

Completed 2026-11-17 in the working tree after internal 0.4.3. No dependency or
SQLite migration, release bump, commit or push was performed in this follow-up.

- Slice CLI/API exposes positive integer timeout seconds and RSS bytes/MiB.
  Existing defaults remain 60 seconds per process and 12 GiB. Actual supervisor
  limits, diagnostics and slice identity use the selected values. Correspondence
  re-extractions preserve them; elevated saved limits require explicit caller
  allowances. Context bridges preserve ordinary allowances and reject elevated
  saved requests rather than silently raising them.
- Stored type-text results bind generation/index identity and query rows in one
  read transaction. Legacy `freshness: stored` remains; `freshnessStatus` makes
  the unchecked policy explicit. Verified type-text uses focused freshness and
  rejects a generation mismatch before returning rows.
- `proof-search index freshness` checks supported inputs against a read generation,
  accepts `--expected-generation`, and reports stored-read/source-validation times.
  It avoids history integrity, storage diagnostics and inventory counts. Source
  validation retains two captures. This is an observation, not a persistent token.
- Docs, bundled skill and shared `codex-skills/ladon` now include a short
  TeX-plus-named-theorem recipe and the resource/freshness distinctions.

## Verification

The main focused run (`final-tests.txt`) passed 24 tests in 144.63 seconds:
resource controls with real Lean extraction/replay, existing custom-node replay,
search provenance and memory diagnostics. The consumer run (`consumer-tests.txt`)
passed all eight existing correspondence/context CLI tests and the positive
expected-generation control. It also exposed a missing-index SQLite exception;
this was corrected to the ordinary operational diagnostic. The final fast run
(`fast-final.txt`) passes all 13 freshness/provenance/supervisor tests, including
that correction. The full repository suite was not rerun.

Initial new tests failed as expected. The first live resource run also rejected
in-flight implementation edits; its two affected tests pass in the stable main
run. Original logs are retained. Existing tests and assertions were not weakened.
Scoped strict complexity/dead-code checks, Ruff, OpenSpec validation and both
skill validations pass. This is root verification, not an independent audit.

The read-only MF status profile attributes 54.631 of 72.778 seconds to hashing
50 historical databases. The new focused command took 5.848 seconds unprofiled
and reported fresh inputs. Different measurement modes and one run per path
preclude a controlled speedup claim. See STATUS-PROFILE.json. Sampled archived
inventories contain lineage evidence; the current active index has no evidence
trigger requiring a new snapshot. Existing archives were not changed.

## Remaining work

Define retention policy and reference-preservation rules before rotating history.
Current `--max-history-mib` is a fail-on-growth cap, not eviction. Consider
retaining the required evidence without a full lexical-index copy per snapshot.
Reusable snapshot tokens need explicit invalidation semantics. Compact slice
projection remains proposed; the retained consumer summary is its initial use
case. These are not automatic schema or caching changes.
