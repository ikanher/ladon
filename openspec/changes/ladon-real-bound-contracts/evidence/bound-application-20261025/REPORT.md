# Exact observed predicate binding

Task 2.1 is verified for the generic prefix family. The public commands now
check predicate equivalence, prefix order and bound monotonicity for the exact
predicate application in a freshly elaborated observed theorem, including its
dependent type and instance parameters. This completes the missing link from
the preceding named-law checker. **Full Real semantic contracts remain
unadmitted; informed cases remain 0/2.** No paper norm, scalar/composition rule,
derivative adapter, theorem-body validation or native consumer was activated.

## Result and evidence

- Three positive generic checks returned `checked-binding`: a polymorphic
  sequence bound, a valid bound with an unused False premise and an alternative
  instance parameter, and a bound using a separate compiled interpretation.
- Eight negative attempts remained unresolved: wrong measure, `sorry`, an
  invalid prefix predicate despite an unused False premise, a forged/rehashed
  expression, a changed definition with the same name, a changed same-typed
  instance, a retained proof parameter and a changed compiled interpretation.
- Two API controls rejected stale source and reuse of a saved success receipt.
- All 172 focused tests passed in 113.36 seconds, including 17 new red-first
  planner/CLI/bounds/universe tests. Ruff, scoped strict quality, OpenSpec strict
  validation and `git diff --check` passed. No whole-repository or paper run.
- The eleven final mathematical attempts took 319.49 seconds in their CLI
  invocations, peaking at 4.186 GiB of process-tree RSS. Each check had a
  600-second deadline and the unchanged 12 GiB cap; there were no resource
  failures in these attempts. These totals exclude planning, initial debugging,
  the incorrectly selected harness case and the compatibility suite.

See [VERIFICATION.json](VERIFICATION.json), [CHECKS.json](CHECKS.json), the raw
case results under `public-matrix/`, `public-matrix-followup/` and
`import-mutation/`, and [the independent source review](REVIEW.md).
The reviewer inspected code and root-produced evidence, not an independent Lean
execution. The attempted red worker failed; no independent red-worker or
portfolio peer-review credit is claimed. Root authored/froze the red tests.

## Mechanism and trust boundary

`plan-bound-prefix` accepts an existing observation plus a named measure and
explicit ordered binder IDs. `check-bound-prefix` compiles the fixed family and
binding helper in a clean private project before copying the selected source.
The Lean term elaborator compares the actual normalized statement to the
observation modulo bound-variable display names, then constructs `Admission`
from the actual predicate prefix. It preserves constants, universe levels,
binder kinds/types, de Bruijn references and instance arguments. The measure's
arguments are typechecked in Lean. Only required parameter dependencies are
universally closed; retained proof-valued dependencies are unsupported.

Fresh source-goal capture, completion, independent compiler replay and the
standard no-placeholder axiom policy establish the generated proposition.
The typed-subject and captured goal structures must agree exactly. Sources,
helper/checker identities and imported inventories are rechecked. No historical
JSON receipt can authorize a future check. A proposed measure need not occur
literally as a predicate parameter: its relation to the predicate is what the
checked equivalence proves. No norm interpretation follows from that relation.

The imported-definition control deliberately rebuilt an imported module with a
different interpretation while retaining the selected source and pinned context
identity. Fresh checking rejected the old equivalence proof. Its raw compiled
inventories and module identities are preserved in the case evidence. Plans are
not imported-definition certificates; the fresh check binds compiled meaning.

The general completion path also needed a universe fix: it now carries original
universe names into submitted-term elaboration and both empty-context reparses.
Independent `u` and `v` survive actual completion and replay. No completion wire
format or historical Nat mathematical profile changed.

## Preserved failures and limits

The earlier 15-minute gate remains historical and its placeholder negative
remains incomplete. The user authorized further work without that aggregate
budget concern. The fresh `sorry` attempt here completed and was rejected for
`sorryAx`; it does not retroactively complete the old run.

Initial live checks found two implementation gaps: hygienic binder display names
changed across source-copy paths, and the generic completion reparser lacked
universe names. The fixed comparison ignores only alpha-irrelevant binder
labels, while generated law binders have stable names for exact capture replay.
A planner hashing failure used the native artifact scalar encoder for snapshots
containing process timings; planning now uses the existing snapshot identity.

The first unused-False positive harness attempt selected instance b1, although
Lean's actual predicate used b2. Ladon correctly rejected it. That attempt and
its original script remain in `public-matrix/`; it is not counted as a passing
positive. The corrected positive and deliberately mismatched instance case are
separate in `public-matrix-followup/`. Frozen fixtures/tests were not weakened.

All 2,670 primary source files and 59 artifacts from the two preceding child
packets are unchanged. The board's one pre-existing mismatch in
`tests/test_rational_lean_encoder_v2.py` remains unrelated and untouched.
The previous law receipts remain historical after the shared completion helper
changed; they are not advertised as current checker results.

Next: task 2.2's guarded Real composition laws, followed by the derivative
adapter and explicit native consumer dispatch. The parent independent-pair,
held-out discovery and evaluation gates remain open. Nothing was pushed.
