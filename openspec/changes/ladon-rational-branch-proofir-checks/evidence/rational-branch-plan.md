# Rational branch plan, native validation, and current gates

The separate `ladon.proof_contract_rational_probes.plan_rational_branch_probe`
API accepts a closed request with independent source and Lean workspace roots, a
validated refinement branch, base rational goal, exact assignment, absolute
monotonic deadline, and bounded process limits. It calls the existing branch
checker, encodes each derived premise and conclusion as a closed rational
proposition, then compiles those propositions using the selected workspace's
pinned Lean and already-built Mathlib with `norm_num`. It does not run `lake
build` or mutate the target workspace. A missing toolchain, Mathlib module, or
incompatible normalization returns `unsupported` with no goals. Zero division
returns `rejected` before goal generation. Expired deadlines and process
resource stops return `incomplete` with no artifact.

Successful plans use schema `ladon-rational-branch-plan-v1` and bind branch and
kind, source-span identities, base and derived goal digests, exact assignment,
generated proposition digests, checker identity, and exact workspace identity
into `planId`. The plan is also emitted as a validated
`proofir.contract-analysis` artifact at stage `rational-branch`, with a
dedicated rational profile digest. Native validation reruns
`encode_rational_goal` from the stored derived goal and assignment and requires
exact checker-identity and obligation equality. This rejects a forged Boolean
obligation even if its goal digest, `planId`, analysis subject, and outer
ProofIR content identity are all recomputed. SQLite projection accepts and
records the new stage.

The frozen acceptance suite is
`tests/test_rational_branch_plan_v8.py` (14 tests). It includes the 13-obligation
mixed-operation matrix, all six comparisons, strict/equality boundaries,
premise/conclusion outcomes, native ProofIR validation, full nested-identity
forgery rejection, an expired-deadline stop, missing Mathlib, zero division,
closed-input rejection, identity changes, and nonclaims. Its exact Boolean
vector is `[true, true, true, true, true, true, true, false, false, true,
false, true, false]`.

Validation completed so far in `/home/codex/projects/ladon`:

- `pytest -q tests/test_rational_branch_plan_v8.py` — 14 passed in 65.92s.
- The combined rational, ProofIR and application-probe set against v8 passed
  124 tests in 77.03s.
- `ruff check` and `radon cc` passed for changed implementation and test files;
  no C-or-worse blocks were reported. Scoped `vulture --min-confidence 80`
  found no findings. Scoped `compileall` passed.
- `openspec validate ladon-rational-branch-proofir-checks --strict
  --no-interactive` passed after the final task/evidence edits.
- Independent audit #411 accepted the narrow post-preflight deadline
  remediation. It reviewed test logic rather than executing it; the root run
  above passed the frozen v8 suite.
- The repository-wide strict quality script passed its static quality, Ruff,
  and compile gates, then its full `pytest -q tests` phase was interrupted
  after about eight minutes while still running. The bounded focused suite
  above is the completed relevant test gate for this slice.
- Independent audit #402 reproduced a forged-obligation acceptance before
  remediation. Native semantic regeneration and the full nested-identity
  forgery regression now pass; audit #409 accepted that fix and expired-at-entry
  gate. Audit #409 also found the post-preflight deadline gap, which was fixed
  and accepted in the narrow follow-up #411.

This remains a planning artifact, not a checked receipt or checked-support
result. It does not establish source-prose fidelity, universal truth, or a
counterexample to the original theorem. Checked-receipt replay/cache binding,
complete worker resource-stop tests, and receipt/cache regressions remain open.
