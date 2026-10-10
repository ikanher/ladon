# Index history candidate-local field replay (r01)

This replay used the working-tree CLI candidate under `uv run ladon`, with no production source or test edits by this replay. All candidate projects, raw command output, stderr, and `/usr/bin/time -v` samples are retained in this directory. `commands.log` records the repeated update edits and invocations; the other direct commands are enumerated below.

## Candidate projects and actions

- `fixture/` is a disposable copy of the Lean source and config from `tests/fixtures/theorem_capsule`, including its small `.lake` contents. It was built through the ordinary index CLI, then `CapsuleFixture.chosen` was acquired with `theorem lineage --refresh always`. Lean reported `authority=lean_environment`, 82 nodes, 172 edges, and a 1.08 s acquisition. A source declaration was added; ordinary `index update` published generation `3f29a4c9…`, extracting one of three modules and reusing two. `search name --text addedAfterEdit` found the new declaration. `index history` listed the archived evidence; `theorem lineage ... --history <snapshot> --refresh never` returned the old closure with `selectionBasis=historical-snapshot` and `currentAssociation=not-established`. A later explicit `--refresh always` acquired a new closure (`4033a45a…`) separately.
- `adam/` contains the transitive Lean source import closure for `Mf.Optimization.FiniteMemoryAdam.CumulativePairing` (86 Lean files, 1,689,982 bytes) and the project config. Its `.lake` is a symlink to the shared checkout's existing compiled cache. No `lake build` ran. Index build and real lineage acquisition both succeeded: theorem `Mf.Optimization.FiniteMemoryAdam.Cumulative.pairing_lower`, 290 edges (32 type, 258 value), 9.89 s acquisition. The source file is `CumulativePairing.lean`, but the actual namespace is `...Cumulative`; the module-path-qualified name suggested in the task does not exist. Nine Mathlib source files in this import closure are absent from the checkout's source tree; their already-compiled imports were available through `.lake`, and acquisition succeeded.
- For each candidate, three measured ordinary updates each followed a unique comment edit in one Lean file. Every update completed and extracted one changed module; fixture reused two modules and Adam reused 85. The first repetition preserved a new evidence-bearing snapshot. The next two produced no additional archive bytes because the evidence snapshot was unchanged.
- `clean-fixture/` and `clean-adam/` are independent clean index builds of the exact final candidate source trees. `logs/lexical-parity-final.jsonl` compares `modules`, all lexical declaration fields, and `module_imports`: fixture 3/77/2 rows and Adam 86/2411/171 rows all match exactly.
- A pre-update SQLite backup was captured immediately before a final fixture source edit. The following update archived it as `a06d9560…`; `compare-retained-rows.py` compared all 59 user tables and found exact row equality. Other archives correctly differ because they represent distinct source/evidence observations.

## Resource samples

Each command has its own `.time` file with wall time, user/system CPU, and maximum RSS. The repeat updates are `fixture-repeat-{1,2,3}` and `adam-repeat-{1,2,3}`. Their measured summaries are:

| Input | Run | Wall | CPU user + system | Max RSS | Extracted / reused | Active DB | History | Temporary DB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Fixture | 1 | 0.22 s | 0.18 + 0.02 s | 37,812 KiB | 1 / 2 | 1,064,960 B | 2,129,920 B | 1,064,960 B |
| Fixture | 2 | 0.18 s | 0.16 + 0.01 s | 40,772 KiB | 1 / 2 | 1,064,960 B | 2,129,920 B | 1,064,960 B |
| Fixture | 3 | 0.19 s | 0.17 + 0.02 s | 37,028 KiB | 1 / 2 | 1,064,960 B | 2,129,920 B | 1,064,960 B |
| Adam | 1 | 0.35 s | 0.29 + 0.04 s | 39,184 KiB | 1 / 85 | 7,651,328 B | 7,651,328 B | 7,651,328 B |
| Adam | 2 | 0.31 s | 0.26 + 0.04 s | 38,916 KiB | 1 / 85 | 7,651,328 B | 7,651,328 B | 7,651,328 B |
| Adam | 3 | 0.30 s | 0.25 + 0.04 s | 39,012 KiB | 1 / 85 | 7,651,328 B | 7,651,328 B | 7,651,328 B |

The table records the CLI-reported temporary database allocation, not a continuously sampled whole-filesystem peak. During the measured updates, the conservative database-only upper bound from one active file + registered history + candidate temporary is approximately 5.3 MB for fixture and 22.9 MB for Adam. It excludes SQLite journals/WAL, lock files, source copies, and filesystem allocation overhead. No speedup claim is supported by these samples.

The 32 GiB process cap was not changed. Individual `/usr/bin/time` maximum RSS records are retained for every command.

## Command trace and interventions

Direct ordinary commands (all outputs and stderr are in `logs/`):

1. `uv run ladon proof-search index build --repo-root <fixture> --format json`
2. `uv run ladon theorem lineage CapsuleFixture.chosen --repo-root <fixture> --refresh always --format json`
3. Add `addedAfterEdit` theorem, then `uv run ladon proof-search index update --repo-root <fixture> --format json`
4. `uv run ladon proof-search search name --text addedAfterEdit --repo-root <fixture> --format json`
5. `uv run ladon proof-search index history --repo-root <fixture> --format json`
6. `uv run ladon theorem lineage CapsuleFixture.chosen --repo-root <fixture> --history <snapshot-id> --refresh never --format json`
7. Explicit `theorem lineage ... --refresh always` acquisition after the edit.
8. Equivalent index build and lineage acquisition for the Adam source-copy project.
9. Three comment-edit / ordinary-update repetitions on each project (`repeat-updates.sh`).
10. Clean index builds for both final projects; exact table parity comparison (`compare-lexical.py`).
11. A further explicit fixture acquisition, SQLite backup, one source comment edit, update, and exact 59-table comparison against its registered archived snapshot (`compare-retained-rows.py`).

One initial search invocation omitted required `--text` and was rejected by CLI argument validation; the corrected public invocation succeeded. The first history-list parser probe expected an `entries` key; the actual contract uses `snapshots`, and the corrected parse succeeded. These interventions and original stderr are retained. No production edits were made by this replay.

The shared matrix-factorization checkout was read for source/config and existing compiled imports only. The replay did not invoke `lake build`; all source edits occurred in disposable copies, and the target `CumulativePairing.lean` remained clean by `git diff`. The checkout was already dirty (2,379 status entries at the first recorded check). A later status comparison found one unrelated concurrent change to `openspec/changes/deterministic-bis-koutoft-production-scaling-umbrella/run-state.md` (69 inserted lines, mtime 09:37 +0300); it was not created or touched by this replay, whose edits and commands are confined to `temp/index-history-field`. Thus the shared source target was untouched, though the shared checkout as a whole changed concurrently during observation. `shared-checkout-status.after.txt` and `shared-checkout-status.final.txt` preserve the comparison.
