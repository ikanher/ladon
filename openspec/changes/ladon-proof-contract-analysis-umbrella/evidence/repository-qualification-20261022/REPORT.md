# Repository qualification and shared skill update, 2026-10-22

Status: **repository implementation qualified; detection benefit remains unestablished**. Umbrella Task 3.2 is complete after the corrected full strict run passed all **4,817 tests** (one expected skip) on the final source-manifest snapshot. The umbrella stands at **9/12** with the current outcome published in `tasks.md`; Tasks 3.3 and 3.4 remain open because the evaluation has no admitted held-out cases and no detection-benefit result. This qualification establishes repository checks and retained contract boundaries, not source fidelity, general analytic lifting, or detection of unfamiliar exposition errors.

## Scope and runtime

The candidate is the actual dirty checkout at observed HEAD
`9695596ed9db287076251649ae57051331f83775`. Public packaging gates use their
supported directory candidate, `/home/codex/projects/ladon`, to include current
maintained untracked files without staging unrelated work. Wheel checks execute
outside the checkout and verify installed import origins. This is neither a
HEAD-only candidate nor an export bypass. Nothing was committed or pushed.

The earlier 3,600-second run (attempt 02) expired without a final pytest
summary. Attempt 03 used a separate two-hour bound, completed the collection,
and exposed one stale generated-matrix test path. An attempted restart (04) was
invalidated during static preflight because its manifest was stale; pytest did
not run. After correcting and freezing the manifest, attempt 05 completed the
full suite in 55:28 with no deselections. Per-attempt receipts and logs are
preserved below. The [current source manifest](final-source-manifest.json)
identifies the exact final files for attempt 05 and does not retroactively
identify earlier snapshots.

## Changes and their justification

The strict baseline stopped before pytest with **24 Radon/maintainability/test
complexity findings**. Rational native validation, workspace selection, checker,
worker, payload validation and restricted-domain matching were decomposed into
bounded helpers. Their closed payload validation, exact goal/source identities,
trust coverage, replay, deadlines and resource stops were retained. No package
dependency or Quux import was added. The eight test helper/import refactors
preserve all **260 assertion ASTs** and all cases; see
[test-refactor-preservation.json](test-refactor-preservation.json).

The installed distribution harness referenced a removed single test filename.
A red regression established the failure, then selection was updated to include
all installed contract test files while still requiring a CLI contract family.
The old single-file layout remains supported. Two regression cases and the
existing gate unit tests pass. Four nonportable documentation paths caught by
the real distribution gate were corrected.

OpenSpec validation exposed one empty orphan directory and missing automation
metadata. Only verified empty directories were removed; 19 packets received
their own strict validation command. No tasks or acceptance conditions changed.
A preexisting pure-refactor packet with explicit `skip_specs: true` was being
misreported as missing a delta. The backlog reader now recognizes a conservative
plain, flat metadata subset, declining unsupported syntax and duplicate keys.
Independent review found an alternate duplicate-key bypass in an intermediate
patch; the retained red controls and final parser correct it. The exemption
affects only that missing-delta finding. Other backlog checks remain active.
See [openspec-metadata-repair.json](logs/openspec-metadata-repair.json).

The first required portable benchmark failed all three stability cases while
its correctness and resource checks passed. A diagnostic run, explicitly not an
acceptance pass, isolated changing `run_resources.observed.peakRssBytes` values
in otherwise equivalent reports. Normalized report comparison now zeroes only
nonnegative exact integers at that registered observation path, on a detached
copy. Raw reports, unavailable values, limits, counts, statuses and values
outside the registered path remain unchanged. The benchmark independently
measures and checks process RSS; no threshold or correctness oracle changed.
The required benchmark rerun passed. Failed and diagnostic attempts remain in
the evidence logs. The saved raw pair has 26 differences: the old normalization
removes 23 timing differences and the corrected normalization removes the
remaining three RSS differences; see [stability-diagnosis.json](stability-diagnosis.json).

## Verified results

| Check | Result | Evidence |
| --- | --- | --- |
| Full Python strict gate, original bounded attempt | Incomplete at the earlier 3,600-second deadline, exit 137; no pytest summary | [command](logs/full-strict-02-command.json), [log](logs/full-strict-02.txt) |
| Full Python strict gate, stale-matrix diagnostic attempt | 1 failed, 4,816 passed, 1 skipped; stale generated path identified | [command](logs/full-strict-03-command.json), [log](logs/full-strict-03-stream.txt) |
| Restart invalidated before pytest | Stale source manifest detected during static preflight; not a test result | [record](logs/full-strict-04-command.json), [log](logs/full-strict-04-stream.txt) |
| Full Python strict gate, corrected final snapshot | **Passed**, wrapper exit 0; 4,817 passed, 1 skipped in 3,288.39 s | [command](logs/full-strict-05-command.json), [log](logs/full-strict-05-stream.txt) |
| Corrected supported-feature matrix | Matrix integrity 5 passed; all listed feature gates 15 passed | [verification](logs/matrix-fix-verification.json), [log](logs/matrix-fix-verification.txt) |
| Final Radon/maintainability/Vulture over `src`, `tests`, `scripts` | Clean, 13.50 s | [quality-final.json](logs/quality-final.json) |
| Final full scoped Ruff | Passed | [receipt](logs/final-verification.json) |
| Rust workspace, locked/offline | Passed, 1.39 s, `PROOFIR_NO_LEAN=1 PROOFIR_NO_QUUX=1` | [command](logs/rust-command.json), [log](logs/rust-tests.txt) |
| Final installed distribution, package resources and contract tests | 41 tests passed, 26.09 s | [command](logs/installed-distribution-final-command.json), [log](logs/installed-distribution-final.txt) |
| Final required installed Lean integration | Passed, 41.71 s | [command](logs/installed-lean-final-command.json), [log](logs/installed-lean-final.txt) |
| Required portable benchmark rerun | Passed, 15.18 s | [command](logs/portable-benchmarks-final-command.json), [results](logs/portable-benchmarks-final.json) |
| Native-validator focused regressions | 40 passed, 1 expensive case deselected | [log](logs/native-root-tests.txt) |
| Checker/domain/probe focused regressions | 64 passed, 1 expensive case deselected | [log](logs/checker-root-tests.txt) |
| Installed harness unit regressions | 33 passed | [log](logs/distribution-unit.txt) |
| Final metadata reader/backlog/hygiene regressions | 32 passed | [log](logs/backlog-tests-final.txt) |
| Final resource normalization/report/benchmark regressions | 48 passed | [log](logs/normalization-root-tests.txt) |
| Report v3 direct consumer | 18 passed | [log](logs/report-v3-consumer.txt) |
| All OpenSpec strict validation | 77 passed, 0 failed | [command](logs/openspec-final-command.json), [log](logs/openspec-final.txt) |
| OpenSpec hygiene and backlog | Zero drift, zero findings | [hygiene](logs/openspec-hygiene.txt), [backlog](logs/openspec-backlog-final.txt) |

The portable benchmark reports zero correctness failures, expected coverage
17/17, zero stability failures, 44.234 MiB maximum measured process RSS, and
passing runtime, cache invalidation, timeout and cancellation checks. These
are the existing portable benchmark population, not a measurement of new
exposition-error detection.

Attempt 03's completed run exposed a stale path in the generated supported-
feature matrix: `test_installed_cli_contract.py` had been removed while its
maintained successor is `test_installed_cli_contract_v2.py`. The generator was
corrected and both generated matrix artifacts regenerated. The matrix-integrity
tests passed 5/5, and the generator's complete feature-gate verification passed
15/15. The final strict run then passed against the manifest that includes this
fix; all tests remained collected. Attempt 02's interruption, attempt 03's
single failing regression and attempt 04's pre-pytest invalidation remain
recorded as historical outcomes, not passes.

## Shared skill and independent review

Updated the canonical sibling skill at `../codex-skills/ladon/SKILL.md`, its
source-goal and verified-discovery references, and added
`references/contract-analysis.md`. The guide routes current public contract
commands, states the supplied-witness Nat/rational fragment, distinguishes fresh
Lean checks from historical saved inspection and ID-only report association,
and preserves source-fidelity and analytic-lifting limits. Default RSS guidance
is 12 GiB with stop-and-report behavior and no automatic cap increase. Explicit
higher profile maxima are retained. Current-checkout runtime selection and
identity guidance remain available. The separate README-linked local
`skills/ladon/SKILL.md` received a small matching routing/resource update.

Both skill validators pass. A fresh blind walkthrough used only the skill,
generic guides and current CLI help, and correctly retained historical
authority, source fidelity, report association and resource-stop boundaries.
It ran no target-specific proof or answer-key evaluation. See
[skill-forward.md](skill-forward.md).

Five distinct Luna-medium workers provided the scout, two implementation
routes, blind skill walkthrough and independent integrated audit. Root owned
production edits and final execution. Reviews #1351/#1354 cover the refactors
and harness; #1364 exposed the metadata bypass; #1366 accepted its correction
and the RSS boundary. These are source reviews and direct probes, not independent
executions of the full suite. [independent-review.json](independent-review.json)
preserves the original board posts and participant metadata, including the
erroneous short-author registration #1330 and its correction #1331.

## Remaining acceptance

Task 3.2 is complete from the full strict pass on the final manifest snapshot.
The independent integrated source review remains scoped to repository contracts
and trust boundaries, not mathematical truth of an exposition. The process-cost
observation is diagnostic only: logical reads include cached reads and are not
physical disk throughput.
The [source-only cost scout](cost-scout.md) identifies repeated exact compiled
closure and freshness checks as candidate costs, without attributing measured
time or reads to one function. Its approximate "27 minutes" describes a later
status, not elapsed time captured in the observation JSON; root correction
#1371 preserves that distinction. The only qualification-driven test-path change updated the generated feature matrix to the maintained versioned test; no identity-cache behavior changed.
The frozen-test registry still has its known unrelated historical mismatch in
`tests/test_rational_lean_encoder_v2.py`; this turn does not repair or conceal it.

Next, continue Tasks 3.3 and 3.4 from the evaluation child: admit and account
for the predeclared cases, then measure detection benefit under its frozen
promotion rule. Parent 2.1 still needs an independently sourced pair reaching
the realizable frontier. The held-out detection track currently has zero
admitted cases; source fidelity, general analytic lifting and unfamiliar-source
detection benefit remain unestablished. No new Navier–Stokes retest, handoff or
audit was started.
