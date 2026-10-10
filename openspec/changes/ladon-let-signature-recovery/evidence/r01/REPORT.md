# Let-signature recovery and runbook alignment

Current state: the requested fixes are implemented, independently audited and verified through both installed runtimes and the actual source owners. Full maintained strict acceptance remains open because two unchanged process-cleanup tests fail intermittently. The user authorized committing these fixes; archive and full release acceptance remain pending.

## Feedback and scope

The supplied archive was located at `../lean/matrix-factorization/temp/ladon-update-feedback-r01.zip` (SHA-256 `9e1e371e84e7ea957145e07d5a41ef939812bb29562a5e7cc54167df8036c9e0`). Its feedback is retained in `FEEDBACK.md`. Existing release and field records are unchanged. The pre-upgrade build timing is not attributed to 0.2.2, and this change does not renew the earlier field's untested compiled-evidence claims.

Two requests are addressed: preserve the conclusion after theorem-type let assignments, and align the mathematical project's runbook with explicit status/update and separate compiled acquisition. The patch release is 0.2.3. No Lean dependency, public command or SQLite schema change is introduced.

## Implementation

`proof_search_signature.py` scans masked statement tokens, tracks balanced binder/nested-term groups, consumes ordinary root let/letI assignments and stops before the declaration body. It supports newline/semicolon let chains, nested initializers, binder defaults and absolute-value conclusions. Literal/comment masks preserve existing source offsets. The 16 KiB ceiling and lexical authority remain. Recognized unsupported root do/have/suffices/recursive-let forms, unbalanced syntax and a missing separate body boundary for declarations needing a body are unavailable with `lexical_signature_unavailable`. Bodyless axiom/constant statements can retain supported lets without requiring a proof assignment. This is a conservative lexical recognizer, not a Lean parser or an applicability check.

The extraction identity advances from lexical-navigation-v3 to v4. Verified old signatures are stale. An explicit update recognizes that exact prior full helper identity, re-extracts all current modules once even without source edits, and uses existing archive/atomic publication ownership. Unknown helper identities fail closed with `full-build-required`. Retained rows are archived, not promoted as current evidence. Subsequent unchanged updates preserve database bytes. Module replacement removes its old declaration omissions before inserting new rows.

The short and external Ladon skills and `../lean/matrix-factorization/docs/LADON.md` explain the upgrade path. The shared mathematical repository's theorem sources, compiled outputs, caches and indexes were not edited or rebuilt. External skill changes preserve its pre-existing memory/architecture edits. `FIRST-HAND-REPORT.md` is unrelated pre-existing work and remains untouched.

## Test-first and independent review

The separate red/scout/green/audit workers used Luna at medium reasoning on the existing project board `.codex/state/ultra-result-evidence.sqlite3`, topic `lexical-let-fix`. Root owns integration and qualification. The red worker's scratch proposal was adapted to the actual v3 predecessor before freezing; additional root tests cover real layout, limits, missing boundaries and omission updates. Frozen records retain their exact hashes.

`red.log`: eight intended failures, two passing controls. `red-layout.log`: one failing real-owner shape. `red-boundaries.log`: four failures. `red-omissions.log`: repeated unavailable omission failed. `red-do.log`: two proof-leak failures found by the independent auditor; `red-missing-assignment.log`: one related failure. The initial green proposal is historical scratch evidence, not the final scanner. Root removed whole-proof balancing and newline inference, and integrated the bounded token scanner. An existing structure/archive test also caught omission replacement; `green.log` retains that failure. The pre-bodyless-flag focused suite (`green-audited.log`) passed 80 tests; the final worker independently ran all 20 new regression cases.

Audit post #1034 found unsupported do-binding leakage. Root fixed it conservatively and added the public-index regression. The initial re-audit passed 18 new tests. Further root and audit review added missing-assignment rejection and a positive bodyless axiom control. Final audit posts #1047/#1048 (`audit-final.jsonl`) passed all 20 new cases, scoped Ruff and all 144 frozen/superseded records with no mismatch. Four final implementation hashes agree with `candidate-hashes.json`; no blocker remains on those bytes.

## Qualification

The final candidate is frozen in `candidate-hashes.json`. The overlapping broad attempt passed 3,305 maintained tests but failed five existing process/deadline cases; Python 3.11 passed all 1,501 affected installed tests, and Python 3.12 passed 1,500 with one startup-readiness failure. All five maintained failures passed in isolation (1.58 s); Python 3.12 cancellation and malformed-output controls passed in isolation (1.34 s). No assertions, deadlines or production sources were changed. The bounded serial retry retained the successful 3.11 qualification, reran full strict and then the entire 3.12 population; its final outcomes are recorded below. These separate executions are not combined into a fictional single passing suite. See `strict-final.log`, `installed-run.log`, `strict-failure-isolated.log`, `installed-312-failure-retest.log` and the serial logs. Earlier strict failure at complexity C11, an interrupted pre-audit strict attempt, and the installed source/wheel mismatch are retained as superseded attempts; none qualifies final bytes. Complexity was reduced with small helpers, without weakening the configured gate or frozen assertions.

## Installed actual-owner replay

`field-replay.py` copied exactly two source files into a disposable standalone lexical project. The installed 0.2.2 CLI built its old signatures; installed 0.2.3 reported stale extractor identity and explicitly recovered both modules with zero source changes. The query for `defaultCarriedMemoryCoefficient` changed from one result to six, including `Mf.Optimization.FiniteMemoryAdam.streamRun_joint_centered_carried_remainder` and the scalar response theorems. The post-recovery no-op retained identical database bytes; final verified freshness is fresh. `field-replay.json` retains source hashes, exact commands, exit statuses, output hashes and GNU time records; selected full JSON outputs are adjacent.

This is a lexical navigation/upgrade replay, not a mathematical check or whole-project benchmark. The copied-owner update took 0.45 s and GNU time reported maximum RSS 37,864 KiB for the command (not an aggregate process-tree peak). The query took 0.43 s. The shared Lean project was neither built nor modified by this replay.

## Final outcomes and remaining qualification gate

The frozen 0.2.3 wheel has SHA-256 `b9823d296666fd95ee1bcf969039ebd9151a9c249b19f4ce6cfb60967841d1cb`. Each packaged runtime file matches source and both installed environments. `serial-qualification.json` records actual origins, version identities and populations. Python 3.11 passed **1,501 affected installed contracts** in 344.44 s (`installed-3.11.log`); the complete serial Python 3.12 retry passed **1,501** in 159.81 s (`installed-3.12-serial.log`). These are separate runtime qualifications, not a combined suite count. All 20 new regression cases and the independent final audit pass.

The full strict run passed Ruff, radon/vulture and compilation checks, but its first test execution had **3,305 passed / 5 failed** in 871.80 s. All five failed cases passed separately in 1.58 s. The bounded serial full retry had **3,308 passed / 2 failed** in 608.04 s. The remaining failures are:

- `tests/test_process_supervisor.py::test_non_streaming_cancellation_reaps_descendant_group`
- `tests/test_target_build.py::test_lake_build_cancellation_reaps_its_process_group`

Both assert that a descendant is no longer live immediately after cancellation; both observed a live PID. Their test and runtime-owner files are unchanged by this fix. These observations cannot be converted into a passing full strict gate by adding isolated passes to the full-run count, and they do not prove every failure is merely host contention. No test deadline or assertion was weakened. The targeted signature/update behavior and all affected installed contracts passed; broader release qualification remains incomplete.

Task 3.2 remains unchecked for that strict gate. The next qualification action is to investigate and resolve the existing process-group cleanup/liveness issue under the owning contract, then rerun strict acceptance on the final candidate. This is separate from the two feedback fixes; there is no new signature or runbook implementation obligation. The user authorized committing this reviewed scope; no full release, archive or mathematical verification claim is made.
