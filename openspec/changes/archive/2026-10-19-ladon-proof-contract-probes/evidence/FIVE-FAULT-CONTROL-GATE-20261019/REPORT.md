# Five-fault/five-control bounded feasibility gate

## Result

The gate reconciled five source-bound discrepancy outcomes and their five
matching controls across all registered probe families. It reloaded and
validated 20 actual raw checker receipts, including each supported status,
accepted replay/trust state, exact generated-goal digest and proof-term digest.
All ten native planning artifacts still have open goals and empty check-run
references. The gate passed in 0.097 seconds, within its 1,800-second
reconciliation bound.

This is an evidence-consolidation gate over preserved source qualifications,
not a fresh proof-search campaign. The selected source-check evidence comes
from four final-code qualifications whose reported elapsed times total
956.734 seconds (15 minutes 56.734 seconds): constant uniformity also
requalified regularity (454.025 seconds), witness dependence (165.004 seconds),
restricted domain (168.594 seconds), and inequality direction (169.111 seconds).
These were separate bounded source runs, so the aggregate does not establish
that one shared-clock execution of all five families would finish in that time.
The gate makes no fresh checker claims; every retained result and raw receipt is
linked by path, hash, goal and term digest in `RESULT.json`.

Four saved historical v1 templates remain explicitly unsupported: constant
uniformity, witness dependence, restricted domain, and inequality direction.
Their actual unsupported result envelopes and hashes are recorded in
`RESULT.json`. The exact accepted v2 fragments remain narrow; alternate ASTs,
domains, relation objects, binder orders and out-of-profile metadata remain
unsupported. No matcher was broadened for this gate.

## Verification limits

The five fault labels describe local non-implication of the encoded
source-bound readings. The five controls establish local implications for the
constructed pairs. This is not a natural-language fidelity evaluation, a
Navier–Stokes paper test, a whole-method claim, or evidence that Ladon can
discover arbitrary exposition errors. It does not establish a separating
family beyond the exact finite calibration already recorded under
`FINITE-CALIBRATION-30M-20261019`.

Run `PYTHONPATH=src .venv/bin/python verify_gate.py` to revalidate the preserved
checker results and unsupported-template records.
