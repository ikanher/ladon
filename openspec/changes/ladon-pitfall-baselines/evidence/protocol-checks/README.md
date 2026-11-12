# Feasibility protocol counterchecks

These are protocol checks, not additional scored cases. The final runner is
pinned by `../feasibility-runner-lock-v1.json` and the r19 acceptance index.

## Current-runner checks

- `timeout-countercheck-v2/countercheck.json`: the current `_request_worker`
  timeout path terminates a synthetic worker process group and retains its
  terminal launcher receipt.
- `partial-index-countercheck-v2/countercheck.json`: a synthetic worker
  qualification failure leaves a terminal case record and a hashed
  `qualification-interrupted` index.
- `policy-rejection-countercheck-v2.json`: in-memory tactic and RSS-bound
  mutations are rejected by the frozen policy check.
- `unresolved-capture-countercheck-v1-r6/countercheck.json`: under the
  preserved runtime, an unparseable goal produces two unresolved worker
  attempts and no established proof.
- `unresolved-host-continues-countercheck-v1/`: the actual host loop retains
  that unresolved first case and completes cases 2–4. Its goal mutation is
  explicitly marked unscored. The later records include accepted proofs, so
  they must remain identified by this countercheck provenance and cannot be
  reused as baseline rows.
- `r18-root-integrity-countercheck-v1.json`: root independently recomputed the
  r18 case, evidence, source, runner, lock, policy and corpus bindings.
- `capture-binding-countercheck-v1.json`: current-runner checks accept a
  successful capture only when it names the expected source digest; genuine
  unavailable captures remain unresolved, while wrong/missing bindings and
  nonzero capture exits fail qualification. This is a protocol check, not a
  scored case.

The v1 timeout, partial-index and policy-rejection receipts predate the final
runner digest. They are historical only; the corresponding v2 receipts replace
them for final-runner qualification.

## Failed setup attempts retained as history

The initial unresolved-capture attempts are preserved rather than presented as
successful checks. Attempts r1–r3 failed before reaching a proof attempt because
of relative paths, a resulting runtime-inventory spill, and an incorrect
bundle path. The one accidental receipt written into the reconstructed runtime
tree was removed, after which the exact frozen inventory check passed. Attempts
r4 and r5 reached the worker and exposed two errors in unresolved-result
handling (`capture: null`, then an uninitialized compiled-module count). The
runner was corrected and relocked; r6 passes. The final host-level continuation
check confirms the complete outcome across the real host loop.
