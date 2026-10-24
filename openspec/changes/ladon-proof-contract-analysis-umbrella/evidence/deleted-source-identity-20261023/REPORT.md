# Deleted-source identity fix and qualification

Status: the source-deletion blocker is fixed and independently reviewed. A
measured full-suite run finished with two failures when the live sibling Lean
workspace changed during rational-branch tests. Both failed cases passed in
isolation and under a read-only source snapshot. The full snapshot rerun was
stopped after 1,074 seconds when work was reprioritized; it had no failure
markers at that point. Umbrella task 3.2 remains open. This work
does not establish evaluation or detection benefit.

## Diagnosis and correction

The [earlier failed qualification](../../../ladon-proof-contract-evaluation/evidence/strict-qualification-20261023/REPORT.md)
reported 43 rational-plan failures because the configured matrix-factorization
workspace no longer contained an indexed Lean source. Further investigation
showed that the diagnostic was the first of many tracked deletions. The rational
goals do not require that particular source: preflight stopped while fingerprinting
the workspace, before checking the generated goals.

The earlier conclusion that the workspace had to be restored was too narrow.
Git's cached path list includes files deleted from the working tree. Ladon should
fingerprint the current source contents, independently of whether a deletion has
been staged. It previously treated these valid modified-worktree states as read
failures.

`src/ladon/lean_toolchain.py` now omits a source entry only when its initial
`lstat`, or an ancestor's `lstat`, reports `FileNotFoundError`. Existing paths
retain the same content framing and digest. All other errors retain their
failure behavior. Dangling or unsafe links remain errors, and a file disappearing
after path observation remains a read failure. Removing or restoring a source
changes the fingerprint and invalidates an old context. Required pins and
explicitly requested source inputs still undergo their own existence checks.

No sibling source was restored, and none of the six existing rational-plan test
files was edited. Their hashes match the previously qualified snapshot in
[original-acceptance-tests.json](original-acceptance-tests.json). The two new
deletion regressions and four safety controls were frozen before integration.
The documented semantics are in `docs/EXECUTION_ENVIRONMENT.md`.

## Verification

| Check | Result | Evidence |
| --- | --- | --- |
| New deletion regressions before the fix | 2 expected failures | [red log](red.log) |
| Deletion, path safety and source-enumeration tests | 59 passed; Ruff and changed-file strict quality clean | [focused receipt](focused-checks.json) |
| Original rational-plan v3–v8 tests | 70 passed in 635.60 seconds, including the previously failing 43 cases | [command](rational-consumers.json), [log](rational-consumers.log) |
| Installed distribution and contract tests | 41 passed; installed package/resource checks passed | [command](installed-distribution.json), [log](installed-distribution.log) |
| Required installed Lean integration | Passed | [command](installed-lean.json), [log](installed-lean.log) |
| Required portable benchmark | 17/17 coverage; zero correctness or stability failures | [command](portable-benchmarks.json), [results](benchmark-results.json) |
| Full Python strict, live sibling workspace | 4,885 passed, 1 skipped, 2 failed in 2,950.79 seconds; both failures returned `source tree identity changed` | [measured command](final-strict-90min-memory.json), [log](final-strict-90min-memory.log) |
| Two failed cases in isolation | 2 passed in 44.74 seconds | [measured command](rational-failures-repro.json), [log](rational-failures-repro.log) |
| Same cases with read-only sibling source snapshot | 2 passed in 41.17 seconds | [measured command](rational-snapshot-smoke.json), [log](rational-snapshot-smoke.log) |
| Full Python strict, source snapshot | Stopped at 1,074 seconds on user reprioritization; partial pytest progress, no pass claim | [measured command](strict-snapshot-memory.json), [log](strict-snapshot-memory.log) |
| Rust verification | Prior pass reused: all 24 maintained Rust source/configuration/lockfile inputs unchanged | [identity comparison](rust-check-reuse.json) |

The checks use the local checkout or a wheel built from that checkout. The
[final-tree source manifest](final-memory-source-manifest.json) records 1,529
maintained paths, including dirty and untracked source files. The live-workspace
run measured a 6.63 GiB sampled process-tree RSS peak, zero swap, no cgroup OOM
events, and no Ladon source-manifest drift. Its two failures came from the sibling
workspace, which had Lean files modified near the failure window. The
[snapshot qualification manifest](snapshot-qualification-manifest.json) adds
copied sibling source and Git metadata to the monitored input set. The snapshot
is mounted read-only at the tests' existing absolute path; its compiled Lake
cache is exposed read-only from the existing location. This is a tested-input
manifest, not the enhanced evaluation runtime archive required by evaluation
task 3.1.

The Mathlib navigation feedback received during this work is reconciled in the
[feedback triage](mathlib-feedback-triage.md). Its same-line `where` signature
defect and v4 index recovery have focused passing regressions. Generated-name
coverage and full elaborated section context remain open.

## Independent review and retained limits

Separate Luna-medium red, green and audit workers used the existing proof-contract
board. Root reproduced the red failures, integrated the production patch and ran
the consumer checks. The independent integrated audit found no material issue and
passed 39 relevant tests; exact reviewed file hashes are in board post 1438.
[Board evidence](board-posts.jsonl) and [participant provenance](participants.json)
retain the assignments and results.

The frozen-test registry retains one unrelated historical encoder-test hash
mismatch, already documented before this work in board post 1416 and the
2026-10-22 qualification. It is unchanged; the new tests and original rational-plan
tests retain their frozen hashes. See [freeze verification](freeze-verification.json).

The earlier failed qualification and successful 2026-10-22 snapshot remain
historical evidence. No evaluation case, blind-paper result, or enhanced arm
freeze is established by this fix. The independently sourced statement-pair and
evaluation/detection-benefit gates remain open. Nothing was committed or pushed.
