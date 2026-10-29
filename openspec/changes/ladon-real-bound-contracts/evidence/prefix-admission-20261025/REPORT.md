# Generic prefix-law feasibility and implementation

The generic law-planning/checking interface is implemented and exercised through
the public CLI. It checks a separately compiled prefix family over arbitrary
objects, parameter sets, point domains and Real-valued measurements. There is no
Navier-specific runtime name, offset or predicate registry.

**Task 2.1 remains open.** The closed goals bind the selected source predicate and
measure declarations, but they are not yet connected to the exact dependent
application in a typed estimate observation. Every result retains unresolved
admission and null contract; no semantic contract, propagation rule, derivative
interpretation or paper-norm bridge was activated.

## Implemented surface

- `real_bound_admission.plan_prefix_admission`: bounded closed requests and three
  exact goals, with source/environment/family identities and no caller acceptance.
- `real_bound_admission_check.check_prefix_admission`: fresh, parent-supervised
  checks in a request-owned private project. Source, environment and implementation
  identities are rechecked. Temporary files are cleaned even on worker termination.
- `LadonRealBound.lean`: generic prefix-family definition, order-prefix and Real-bound
  monotonicity proofs, and an adapter from checked predicate equivalence.
- Public `plan-prefix-admission` and `check-prefix-laws` commands, documented in
  [typed bound observations](../../../../../docs/REAL_BOUND_CONTRACTS.md).

The trusted family is compiled before target commands are loaded. Target source
is copied, not replaced by a stale target object. Imported compiled roots are
read without dependency installation/builds. A reserved-family module collision
is rejected. The checker uses the existing source-goal capture, independent
completion/replay and standard no-placeholder axiom policy. Each proof also
checks the generated and captured proposition structures agree. Compiled import
inventories must remain equal throughout the three checks.

## Bounded mathematical gate

The shared 15-minute gate and 12 GiB cap are recorded in `gate-clock.json`; there
was no reset or cap increase. A frozen unrelated sequence fixture first failed
because the new family module did not exist. The family and adapter then compiled.
Fresh individual checks established all three requested goals:

| Goal | Result | Seconds |
|---|---|---:|
| Predicate equivalence | completed, independently replayed | 30.77 |
| Order-prefix weakening | completed, independently replayed | 30.23 |
| Real-bound monotonicity | completed, independently replayed | 30.51 |

Each observed only `propext`, `Classical.choice`, and `Quot.sound` under complete
trust coverage. The initial API consumer passed before the final implementation
identity hardening; that evidence is retained as earlier evidence.

The final **public CLI** then completed all three goals in **100.28 seconds**, with
**4.17 GiB** observed peak RSS. `public-result.json` records `checked-laws`, but
still `admission: unresolved`, `contract: null`. The outer CLI and worker process
receipts are retained. Per goal there are two capture receipts and four completion
receipts, plus the separate preliminary typing receipt.

A same-named source predicate with `j ≤ n` replaced by `j < n` caused the unchanged
adapter to fail Lean elaboration. The original source was preserved. A late
`by sorry` negative attempt exhausted the remaining shared budget during fresh
recapture and was terminated. It is **incomplete**, not an observed placeholder
rejection or passing trust control. No retry was launched. The positive feasibility
result does not close this negative-control gap or establish full admission.

## Verification and review

The focused suite passes **110 tests in 12.98 seconds**, covering the 83 prior
observation/Nat/native contracts and 27 new planning, preflight, CLI and source
freshness controls. Test-first evidence preserves 11 missing-planner failures,
12 missing-checker failures, two missing-CLI failures and the missing Lean module.
Two additional source/environment tests were added after implementation and are
regressions, not claimed red-first evidence. The environment unit control replaces
the context provider; it is not a live compiled-dependency mutation test.

Ruff and scoped strict quality pass for new Python code/tests and the modified
CLI. Strict OpenSpec validation and whitespace checks pass. No whole-repository
suite, paper audit, cache or new package dependency was introduced. Nothing was
pushed.

Independent source review #1575 found no concrete defect in this partial surface;
it did not execute tests or Lean and explicitly did not accept full task 2.1.
The initial two-worker proposal wave had an attribution collision and was not
credited as independent contract review; #1573 records that coordination error.
Root executed all reported verification.

`VERIFICATION.json` confirms 2,670 primary files, 21 prior shape-evidence artifacts
and the historical Nat contract runtime are unchanged. Frozen new tests match;
the unrelated pre-existing rational-encoder frozen-file mismatch remains. The
verification script initially miscounted completion-only receipts; the corrected
accounting uses the recorded two capture plus four completion receipts without
changing product evidence or tests. `IMPLEMENTATION.json` binds this revision.

## Next gate

Bind the observed predicate application, including its dependent parameters,
instances, function/set identities and quantifier scope, to the generated
prefix-law goals using an exact Lean check. Finish the placeholder and live
compiled-environment negative controls before admission. Preserve current
observations and historical law receipts; never promote a saved receipt or checked
abstract law alone. Composition and the derivative adapter remain separate tasks.
Child progress remains 2/8 and the parent remains 8/12. Informed formal contracts
remain 0/2 admitted; unfamiliar-source discovery benefit is unmeasured.
