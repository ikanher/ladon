# Rational branch receipts and replay evidence

The explicit rational-branch check route now regenerates its plan and exact
closed goals, binds branch/source/base/derived-goal/assignment/checker/workspace
identities into receipts, and runs every supplied proof through the bounded
Lean capture, completion, independent replay, and trust path. Each real accepted
goal emits a separate `proofir.check-run` artifact carrying a digest of the
captured compiled-module inventory and compact process/replay evidence.

An independent integrated audit found that a structurally matching caller-made
cache could set public `accepted`, `completed`, `replayed`, and `trusted` fields
and bypass Lean. The checker now treats `cached_result` as informational only;
it cannot authorize support or skip fresh worker replay. A regression constructs
that forged object and forces the worker to time out, verifying that no checked
support or receipt is returned. This also ensures accepted cache-like inputs
cannot lose their per-goal check-run artifacts. Cache acceleration remains
disabled until Ladon has an authenticated provenance mechanism.

The plan's workspace identity binds the pin-selected Lean executable digest and
compiled-library root paths. Planning now runs the bounded Lean preflight on
each call instead of memoizing its prior success, so replacing a compiled file
cannot reuse a stale preflight result. The plan ID still does not hash every
`.olean` file in advance, so it can remain the same across in-place compiled
library replacement. The actual per-goal check-run and overall receipt record
the digest and count of the compiled import inventory observed during capture;
source-goal capture and completion verify that inventory remains stable around
their respective runs. All goals in one receipt must report the same inventory
digest. Every proof invocation performs fresh Lean replay, so stale public cache
data cannot transfer acceptance across changed compiled libraries.

The independent re-audit also found that the result builder silently omitted a
check-run when accepted worker output lacked evidence. It now rejects that
attempt before publishing support. The deterministic worker fixture supplies
bounded evidence and verifies artifact creation; a separate negative test strips
that evidence and requires rejection. The real local Mathlib integration checks
that every accepted goal has a corresponding artifact and receipt reference.

Validation on 2026-10-21:

- Combined focused rational, ProofIR, application-probe, receipt/cache and resource regressions — **131 passed, 1 skipped in 157.45 seconds**.
- `LADON_RUN_SLOW_TESTS=1 pytest -q tests/test_rational_branch_receipts_v3.py::test_local_mathlib_generated_propositions_replay_without_network -s` — **1 passed in 180.71 seconds** against the local pinned Mathlib workspace; the test confirms both generated goals have check-run artifacts and receipt references. No network or model was used.
- Scoped Ruff and `compileall` over the four rational-branch production modules and the receipt test — **passed**.
- `openspec validate ladon-rational-branch-proofir-checks --strict --no-interactive` and scoped `git diff --check` — **passed**.
- Independent audit confirmed the forged-cache and missing-artifact issues are closed. It notes the plan-ID-only `.olean` identity caveat above; checked receipts and check-run artifacts bind the actual captured inventory.
- Frozen acceptance-test SHA-256: `a4ce60b74e61fe50d493f44c7215e591236022cf5ff019d9815f77c2fe3392dc` (`tests/test_rational_branch_receipts_v3.py`).

The route establishes only the generated closed propositions for one finite
rational assignment. Source-prose formula fidelity remains unverified; checked
support neither proves nor refutes the original theorem. Full repository tests
and broader application-probe integration are outside this focused gate.
