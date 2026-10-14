# Tasks

## Current state

Implementation complete and verified: 149 tests, public CLI demonstration, source-preservation checks, and independent final audit accepted after the last production edits. Fresh restart workspace prepared. Detection benefit remains unmeasured; stop before the user’s fresh retest. Evidence: `evidence/REPORT.md` and `evidence/verification.json`.

## 1. Preserve the failure and freeze the gate

- [x] 1.1 Bind the failed retest and previous pilot without rewriting them; verify baseline digests and unrelated worktree preservation.
- [x] 1.2 Freeze regression tests for premature finish, exact contracts, unresolved follow-up and source integrity; observe expected failure before implementation and independent challenge.

## 2. Deliver the investigation loop

- [x] 2.1 Implement source-scoped initialization, bounded validation and actionable scheduling; verify missing contracts and unexamined units remain visible in focused tests.
- [x] 2.2 Integrate init/status/next/finish into installed lightweight dispatch; verify premature finish fails, exhausted/blocked outcomes remain incomplete, and malformed/stale inputs reject.
- [x] 2.3 Document and exercise a portable quantitative contract comparison and faithful control; verify exact values/counterpart bindings and distinct attributed statement/method judgments through the public CLI.

## 3. Make a clean restart usable

- [x] 3.1 Update generic procedure and packaged Ladon skill with the mandatory loop; verify examples run and no target diagnosis enters neutral guidance.
- [x] 3.2 Prepare separate primary-only restart inputs and a hint-free handoff; verify input identities, absence of older runs/solutions and preservation of original experiments.

## 4. Close implementation honestly

- [x] 4.1 Run focused/integration/quality checks and independent integrated audit against final changes; verify bounds, source bindings, exit behavior and no existing-schema regression.
- [x] 4.2 Reconcile strict OpenSpec validation and deliver implementation evidence; verify no fault-detection success is claimed and stop before another answered or scored retest.

## Verified implementation locations

- 1.1: `evidence/baseline.json`, `evidence/verification.json`; four old-report digests replayed unchanged.
- 1.2: `tests/test_investigation_cli.py` (initial absent-command red), `tests/test_investigation.py` (independent proposal and peer challenge), `tests/test_investigation_binding.py` (targeted mutation and symlink red/green); board posts9–28.
- 2.1–2.2: `src/ladon/investigation.py`, `src/ladon/investigation_cli.py`, `src/ladon/entrypoint.py`, `src/ladon/cli.py`; focused plus installed/general parent tests passed.
- 2.3: `scripts/demo_investigation.py`, `docs/INVESTIGATION_LOOP.md`; authored quantitative mismatch and faithful control replayed through public CLI.
- 3.1: `docs/CORRESPONDENCE_DISCOVERY.md`, `docs/INVESTIGATION_LOOP.md`, `skills/ladon/SKILL.md`; mandatory next/finish loop and explicit nonclaims.
- 3.2: external `/home/codex/projects/navier-stokes-retest-v2/`; `evidence/restart-identities.json`; paper digest and all 2669 primary file bytes verified against original export, no old runs copied.
- 4.1: `evidence/independent-audit.txt`, `evidence/stale-binding-mutation.txt`, `evidence/verification.json`; final auditor accepted fixes and parent consumer.
- 4.2: `evidence/REPORT.md`; strict OpenSpec validation and apply-task reconciliation; no detection claim or answered retest.
