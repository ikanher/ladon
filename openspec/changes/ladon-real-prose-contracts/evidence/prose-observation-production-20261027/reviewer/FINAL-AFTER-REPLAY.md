# Replay boundary review

Reviewed the replay change at board post 1897 and the refreshed
`FINAL-REVISION.json` on 2026-10-27. Every listed production, documentation, and
test file hash matches its current bytes.

Replay starts its monotonic clock before historical snapshot validation and
passes that absolute deadline, the exact prior snapshot, and the exact original
interpretation/context request in the same worker job. The supervised worker
validates the previous snapshot, enforces exact request equality, then performs
current source/context/toolchain/compiled-inventory freshness checks before
preparing and running the new observation. A freshness failure aborts the
worker path; it does not continue into observation. The caller does not invoke
root-aware inspection before starting the replay budget, so replay freshness
does not reset the clock or occur outside the supervised process tree.

The added boundary regression checks that the submitted worker job contains the
previous snapshot, its deadline matches the supervisor bounds, and a simulated
outer timeout yields unavailable without launching dependent work. The three
non-object parser regressions remain intact. This review did not run tests,
Lean, or builds; it is based on source inspection and the checkpoint hashes.

No actionable issue found in the replay boundary. Existing limitations remain:
saved receipts are unauthenticated, and this observer does not establish native
Real-shape support, prose fidelity, admission, or formal connection. Final
runtime qualification remains separate from this source audit.
