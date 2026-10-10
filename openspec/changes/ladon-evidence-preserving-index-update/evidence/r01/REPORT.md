# Evidence-preserving index update — release 0.2.2

## Outcome

Explicit `proof-search index update` now preserves a supported evidence-bearing base as a standalone, digest-named SQLite snapshot before publishing current lexical data. The active catalog retains the original observation identities. Current search does not borrow historical semantic fields, lineage or checking results. Update invokes no Lean.

`index history` lists registered snapshots and unregistered/uncertain files separately. Explicit `theorem lineage NAME --history SHA256 --refresh never` inspects a selected original observation offline through an owned read-only copy. Its separately versioned wrapper marks current association as not established. An already-stale closure remains unavailable. Ordinary current-mode schemas remain unchanged.

This addresses the exercised author need: refresh lexical search after edits without discarding stored evidence. It does not establish comparative productivity, mathematical correspondence, human understanding or automatic proof reuse.

## Storage and authority contract

Private schema v6 recognizes the exact supported v5 layout. Changed v5 inputs migrate after preservation; no-op keeps the active bytes and existing version. Unsupported layouts, toolchain/config changes and arbitrary evidence extensions fail closed. Old 0.2.1 readers reject v6.

A SQLite backup preserves every user-table record, including FTS tables and catalog rows; the snapshot is a consistent standalone database. Backup can change SQLite header housekeeping bytes, so the original file digest and snapshot digest need not match. All-table record equality, archived content hashes and no-op active byte stability are separate assertions.

Snapshots live in `<index-filename>.history/`; the database and adjacent directory must move together. Catalog paths are relative, content identities are exact, and historical reads verify owned bytes and actual schema/metadata. Missing, corrupt or substituted registered snapshots prevent update. Interrupted backups remain protected and visible. An optional history ceiling counts existing/uncertain files and proposed snapshots without eviction; the base-build ceiling governs the active candidate.

Supported mutation paths use the common publication lock. Rebuild/prune protect history owners and unknown evidence. Direct snapshot paths and symlink aliases cannot become publication destinations. Existing hardlinked mutation destinations are unsupported, preventing an in-place writer from altering another linked file. Low-level connection APIs still require their owning caller's serialization; this is not a sandbox against arbitrary local Python or filesystem mutation.

Snapshots are synced before active replacement. Pre-replacement failures retain old active bytes; post-replacement durability uncertainty is reported honestly. Source-change diagnostics list a bounded sample and advise retry after edits settle. History deletion, watchers, selective compiled reuse and new search/proof engines remain deferred.

## Test-first and audit evidence

The durable engineering board is `.codex/state/ultra-result-evidence.sqlite3`, topic `index-history`. The actual red/scout/falsifier/green/audit workers used Luna at medium reasoning; root integrated and reran the code. Final audit acceptance is post 1007, retained in `final-audit.jsonl` (focused 20-test audit). The audit was distinct from test/implementation authors.

Original behavioral failures are retained in `red-initial.log`, `red-publication.log`, `red-corrected.log`, `red-audit-controls.log`, `red-prune-unknown.log`, `red-immutable-destination.log` and `red-hardlink.log`. Follow-up controls cover semantic data embedded in declaration/structure rows, budget bypass, orphan inventory, malformed metadata, arbitrary-table/column prune protection, and direct/symlink/hardlink snapshot mutation.

The old retained-evidence refusal expectations were explicitly superseded for supported layouts; unknown layouts still refuse. Original tests are in `historical-tests/`. One erroneous blank-rendered-type expectation was independently corrected to clean lexical parity (board 994). Assertion-preserving quality refactors are recorded in `assertion-refactor.json`. `frozen-tests-final.json` verifies the board's frozen contracts. Tests were not weakened to obtain green.

## Final qualification

The built 0.2.2 wheel passed 1,481 affected installed tests on Python 3.11 (102.37 s) and 1,481 on Python 3.12 (111.34 s). Its SHA-256 is `34dcedc9df9460088005a709f077e23532f7e075d6f826eb28a499641ceddfbc`; installed origins, complete wheel/source byte equality and runtime results are in `installed-check.json`. Runtime and tests are frozen in `final-candidate-hashes.json`. The final maintained strict run passed: **3,290 tests**, Ruff, radon/vulture and compilation checks, exit 0 (`strict-accepted-final.log`, 409.90 s). This is one complete final qualification; earlier runs are not added to its count. Earlier strict runs and installed attempts belong to their own candidate bytes; they are not substituted for final qualification. One full strict trial caught the existing future-ProofIR prune diagnostic regression; another installed attempt correctly rejected source/wheel mismatch after the hardlink repair. Both are retained as historical failures/intermediate work.

`installed-check.py` builds the 0.2.2 wheel, installs it in clean Python 3.11/3.12 environments, verifies installed origins, checks dependencies, and compares every packaged runtime file with source and installed bytes. Both skill copies validate using the skill-creator validator. Version and lock metadata agree at 0.2.2. No new runtime dependency was introduced.

## Real ordinary workflows and cost

`installed-workflow.py` runs from the actual disposable project directory with `--repo-root .`: explicit acquisition, source edit, ordinary update, search, history listing, historical selection and separate fresh acquisition. It checks all 59 user tables against the archived base, historical closure identity and distinct new acquisition. Thirteen recorded commands include an older-reader rejection. Lean acquisition keeps the 32 GiB cap; no shared `lake build` runs.

The small input is an actual Lean-acquired CapsuleFixture closure. The Adam input is a disposable 86-source import closure for `Mf.Optimization.FiniteMemoryAdam.Cumulative.pairing_lower`. It uses the shared project's existing compiled imports read only. Nine Mathlib source files were missing from the observed source tree, while their compiled imports were available; this limitation is preserved in `field/REPORT.md`. Edits occur only in disposable copies. The shared checkout already had concurrent dirty work and changed independently during observation; whole-checkout byte stability is not claimed.

`measure-installed-updates.py` records three ordinary updates per input. Each run preserves all newly archived table records and every existing archive digest, and matches a fresh clean index's modules, complete lexical declaration fields and imports. Raw outputs and GNU time records, including user/system CPU and maximum RSS, are under `installed-measurements/`. A controller samples temporary/journal/WAL files every millisecond; sampled peaks are lower bounds that may miss short allocations and exclude source copies, locks and filesystem block overhead. There are no timing assertions or speedup claims.

Older development measurements remain in `field/REPORT.md`: three fixture updates took 0.18–0.22 s and Adam updates 0.30–0.35 s on the shared host. These are observations, not a benchmark claim or final candidate renewal. `temporary-disk-samples.json` likewise labels its sampled lower-bound scope. Final installed samples are separate and all pass their preservation/parity checks (`installed-measurements/samples.json`):

| Input/run | Wall | CPU user/system | Max RSS | Extracted/reused | Active | History | Temporary DB | Sampled temporary/sidecar peak |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Fixture 1 | 0.20 s | 0.16/0.02 s | 37,900 KiB | 1/2 | 1,077,248 B | 6,414,336 B | 1,077,248 B | 1,463,536 B |
| Fixture 2 | 0.17 s | 0.14/0.02 s | 38,444 KiB | 1/2 | 1,077,248 B | 6,414,336 B | 1,077,248 B | 1,291,168 B |
| Fixture 3 | 0.18 s | 0.16/0.01 s | 38,324 KiB | 1/2 | 1,077,248 B | 6,414,336 B | 1,077,248 B | 1,291,168 B |
| Adam 1 | 0.38 s | 0.29/0.07 s | 40,508 KiB | 1/85 | 7,651,328 B | 30,605,312 B | 7,651,328 B | 9,519,760 B |
| Adam 2 | 0.34 s | 0.28/0.04 s | 39,032 KiB | 1/85 | 7,651,328 B | 30,605,312 B | 7,651,328 B | 9,223,672 B |
| Adam 3 | 0.32 s | 0.26/0.04 s | 38,968 KiB | 1/85 | 7,651,328 B | 30,605,312 B | 7,651,328 B | 9,223,672 B |

History totals include the accumulated earlier genuine observations; they are not per-update additions. Only the first measured edit per input archived the newly acquired evidence, while later lexical-only updates reused the catalog. Final acquisition took 1.74/1.56 s for the fixture and 25.64/13.30 s for Adam on this shared host; GNU-time maximum RSS was about 1.92 GiB and 8.00–8.10 GiB respectively, below the 32 GiB cap. These RSS values are not simultaneous aggregate process-tree peaks. All raw acquisition times remain in `installed-workflow/`. No comparison or general performance claim follows from these observations.

## Handoff and limits

One packet refresh initially tried to include its own not-yet-written redirected JSON result; strict parsing rejected the empty file. The harness now excludes its post-build metadata, and packet validation was rerun. This was a packaging failure, not a runtime or qualification failure.

The delta review packet continues `ladon-active-index-review-data-r02.zip` as r03. It supplies exact runtime/tests, OpenSpec artifacts, both skill copies, release metadata, diagnostic feedback, qualification and measurements. It omits databases, wheels, compiled caches, complete external Lean imports, virtual environments and rendered artifacts. The `acquired-source/` owners reconstruct the source at final acquisition by removing only the three later recorded measurement comment suffixes; each SHA-256 matches the corresponding archived module identity. The packet also supplies later disposable excerpts separately. Reading the materials needs no model subscription; replaying acquisition needs the actual pinned environment. Hash validation does not authenticate the producer, renew execution or validate mathematical exposition.

The package remains uncommitted and unarchived. Unrelated `FIRST-HAND-REPORT.md` changes and adjacent skill architecture-memory edits are preserved. The next decision is review of this bounded maintenance and whether real feedback justifies further work; no automatic feature follow-up is implied.
