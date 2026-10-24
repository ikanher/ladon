# Shared-deadline rational refinement sessions

## Current accepted result (2026-10-22)

Task 2.3 is complete for the supported exact-rational refinement operation. Independent follow-up review #1193 accepted `ladon.proof_contract_refinement_session.run_rational_refinement_session` after the initial audit's input-boundary finding #1186 was fixed. The original single-pass API remains compatible; its historical evidence is retained below.

The new public Python API searches the base goal and applies up to three supplied constraint batches after finding countermodels. Every transition creates a cumulative immutable branch, checks the previous witness against its derived goal, and searches that actual new goal. The original finding remains anchored to the first checked countermodel. Source-cited constraints retain unverified formula fidelity; proposed repairs retain their distinct label. This loop does not generate constraints, lift a model to an original source context, or prove spuriousness.

All rounds share one finite absolute monotonic deadline, at most 256 total candidate attempts, 32 total predecessor reduction attempts and four rounds including the initial search. Initial minimizer rechecks and transition attempts are counted separately, at most four and three respectively. Completed transition checks are distinguished from attempts rejected during validation. No stage derives a replacement deadline or restores a spent work budget. Source validation and individual exact checks are synchronous operations with cooperative deadline polling at their boundaries; a completed atomic check is retained even when the next boundary observes expiry.

Exhaustion preserves earlier findings, exact search prefixes, checked witnesses, incomplete minimization and pending transition evidence. A final-round interruption remains a resource stop. If minimization has not rechecked a newly found witness, the session retains the witness already checked by search. Undefined arithmetic becomes a terminal `invalid-input` attempt with its error and failing assignment, preserving the earlier checked prefix. Optional `capture_invalid=True` enables this behavior in the existing search/minimizer APIs; their default exception behavior is unchanged. A captured invalid search row has a null check summary, and a failed initial minimizer check does not count as a predecessor reduction.

Inputs use the existing bounded JSON-native validation and are snapshotted before exact work. The source root is validated and resolved to an existing directory at entry, so malformed roots fail before search and relative paths cannot be rebound by later working-directory changes. A source citation that becomes stale at a reached transition still returns a partial-history `invalid-input` result.

Finite survival is bound to the final encoded goal and declared candidate family. The documented three-round example preserves witnesses `x = 0` and `x = 1`, then survives four assignments under a proposed `x >= 2` repair. It uses seven candidate checks, one predecessor attempt, two minimizer rechecks and two completed transition checks. It makes no universal, source-fidelity, original-refutation, or spuriousness claim. The runnable example and public API contract are in [the rational branch guide](../../../../docs/RATIONAL_BRANCH_PROBES.md#finite-refinement-sessions-python-api).

### Verification

- Five new frozen test files contain **37 cases**, covering actual cumulative rounds, shared work limits, deadlines, retained witnesses, undefined arithmetic, native input bounds, stale citations and source-root identity. The root observed the missing-API failures, then six stop/input failures in the initial implementation and five source-root failures before their respective fixes. Evidence is recorded on the engineering board in #1170, #1179 and #1188; the tests were not weakened.
- Root and independent reviewer both ran the focused rational/refinement and checked-receipt consumer selection: **172 passed, 1 slow integration skipped**.

```sh
pytest -q tests/test_rational_refinement*.py tests/test_rational_witness*.py \
  tests/test_proof_contract_refinement*.py \
  tests/test_rational_branch_receipts_v3.py \
  tests/test_rational_branch_stale_identity_v3.py \
  tests/test_rational_branch_checked_artifact.py \
  tests/test_rational_branch_checked_reporting.py
```

- Changed-file Ruff, Radon, Vulture and `strict_quality_issues` passed for both production modules and the five new test files; all changed functions are B or better. Compilation, the executable documentation example, and `git diff --check` passed.
- All five new frozen test digests match. The aggregate registry still has the pre-existing unrelated `test_rational_lean_encoder_v2.py` mismatch; it was not modified by this work.
- An overbroad historical plan-test selection was interrupted after 23 passes in 97.63 seconds. It is not counted as a completed qualification. No full-repository or new Lean integration claim follows from the focused run.
- No dependencies were added. Current runtime/test hashes are preserved in `.codex/state/refinement-rounds/integrated.json`; canonical review and lifecycle records remain on `.codex/state/ultra-proof-contract.sqlite3`.

## Historical single-pass slice

The earlier milestone implemented `ladon.rational_witness.run_rational_witness_session`. One finite absolute monotonic timestamp is carried through at most one exact rational candidate search and its optional declared-relation minimization. The session does not derive a duration, reset a clock, or restart a completed stage. The minimizer consumes the candidate search's canonical goal and declared-family snapshots, preserving the checked input identity across the stage boundary.

Candidate and reduction checks poll immediately before each exact check. A check already in progress completes atomically and is included in the trace. Exhaustive finite search remains `survived-declared-scope` when its final check completes after the deadline; incomplete prefixes report `deadline-exhausted` or `budget-exhausted`. A found counterexample remains the aggregate session outcome if minimization cannot start or is interrupted. The minimization result separately reports its incomplete status and preserves only checked assignments. Minimality is not claimed for an interrupted scan.

That API still reports stage counts and a round count of zero before the first candidate check or one after it begins. Its `roundsSupported` is always false. At that milestone, Task 2.3 remained open for genuine rounds and a checked constraint operation; the later rational branch checker supplied the constraint semantics used by the new session above. No CLI/report workflow was added by the single-pass slice.

## Verification

- Frozen active regression `tests/test_rational_witness_session_v5.py`: **26 passed**; superseded predecessor drafts are preserved under `.codex/state/refinement-budget-red/superseded-tests/`.
- Focused rational witness and refinement suite including the session, candidate search, minimizer, immutable branches and lift-result evidence tests: **69 passed**.
- Independent audit #1109 accepted implementation report #1108 against frozen contract #1104. The auditor also ran a broader relevant rational-witness regression selection (152 passed); their review and precise selection are recorded on the engineering board.
- Ruff passed for `src/ladon/rational_witness.py` and the active frozen regression. Radon reports no changed production or test function above B.
- Frozen test registry verification passed with the active v5 SHA-256 matching.

## Remaining scope

Checked original-context lifting and spuriousness proofs (Task 1.3), and the public refine/inspect workflow with a proved-spurious example (Task 3.1), remain open. The new session does not discharge those gates. Full-repository strict quality and measured detection benefit are not established by this focused work.
