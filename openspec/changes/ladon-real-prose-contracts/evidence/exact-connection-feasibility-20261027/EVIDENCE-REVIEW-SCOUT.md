# Evidence review for post 1963

## Findings

The closeout report is appropriately non-green. It distinguishes the accepted
underlying five-order source-goal completion from the outer
`correspondence_check._check_goal` decision: `_check_goal` still declines because
the raw typed-subject and captured-goal fingerprints differ. The offline
binder-name-insensitive equality is diagnostic only. Attempt 3 does not support
an alpha-normalized acceptance rule: it makes the raw fingerprints agree but
then fails closed-target roundtrip. The four-order attempt fails at the actual
`shiftFour n` versus `n + 5` input application. None of these outcomes establishes
mathematical falsity or source fidelity.

The recorded attempt table matches `VERIFICATION.json` and the four top-level
process receipts. Each outer process returned 0 with no timeout, RSS or output
stop; elapsed times total about 299.1 seconds, and maximum outer process-tree
RSS is about 6.19 GB. Nested capture/completion receipts in the five-order
result also show successful returns and no resource-stop flags; the accepted
completion has complete replay coverage and only the three allowed standard
axioms. `run_probe.py` reads the single persisted monotonic deadline before
each launch and passes only its remaining time. The later analysis expiration
does not justify a retry. These are recorded-evidence checks, not an independent
rerun of the root verification script.

The size finding is also properly qualified: the 9.19 MB pair exceeds the
8 MiB raw process input limit; the 5.06 MB DAG measurement is an exact
round-trip prototype, not a production decoder or accepted history policy. The
report preserves the failed 8.81 MB attempt's recorded error/configuration
without presenting its later-edited source as a frozen artifact. No expanded
32 MiB decoder bound has been enabled.

## Next route

The next bounded engineering objective should be a new exact-owner goal
constructor that creates the **single final proposition** from the validated
formal declaration type, authored definition value, and ordered typed
premises, then captures that exact generated target and calls
`capture_source_goal` plus `complete_source_goal` directly. Keep all source
range/copy-origin, context/import/toolchain inventories and proposition Expr
comparisons inside the constructor/replay contract. Do not alter
`_check_goal`'s acceptance predicate to ignore binder names. If product
integration must continue through `_check_goal`, first isolate why its
type-subject and selected-goal representation differ and fix the producer so
both refer to the same owner-checked Expr; do not treat alpha-equivalent
diagnostics as a kernel acceptance certificate.

That follow-up remains a feasibility/API boundary task until it has adversarial
owner/range/import tests and a separately budgeted positive five-order and
negative four-order run. It must retain the formal theorem only as the explicit
conditional premise, keep the coordinate norm factor's real dependency scope,
and preserve rejected-route semantics. No public connection producer,
fresh-admission orchestration or full generic/informed qualification is shown
by the current evidence.

This review read the saved report, diagnostics, verification summary, probe
result and process receipts. I ran no tests, Lean, builds, or hash-verification
script and changed no production or probe source.
