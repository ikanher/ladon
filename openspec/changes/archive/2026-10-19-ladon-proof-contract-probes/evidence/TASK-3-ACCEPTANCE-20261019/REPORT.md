# Tasks 3.1–3.2 acceptance evidence

## Result

The investigation report preserves three different outcomes without joining
their authority:

- A checked `Fin 5 → Nat` transport through `Fin.val` accepts all six recorded
  correspondence checker rows. The native bundle retains six `checkRunRefs`.
- The report projects that bundle as
  `recorded-links-complete-unreplayed`. Its attributed control remains
  statement `aligned`, method `different`, and formal support
  `recorded-links-only`.
- A separate source-bound application observation is attributed as a mismatch
  with no attached formal source or checker receipt. It remains
  `formalSupport: not-established` and `mathematicalFalsity: not-established`.

The report-wide result remains `mathematicalFalsity: not-established` and
`wholePaperCertified: false`. The exact checked membership-erasure
non-equivalence is a separate constructed Lean control; it is not attached to
the application observation and supplies no evidence for that observation.
The stored bundle, plans, report projection, non-implication output and
source-hash manifest are in this directory. Run
`uv run --locked python build_report_evidence.py` from the repository root to
rebuild the packet from the local fixtures and current checkout. The read-only
`verify_manifest.py` checks all 20 recorded input, producer and output hashes,
validates the checked receipt/report claims, and rebuilds the report projection
from the saved plans without replaying Lean. The producer hashes cover the test,
builder, verifier, report, and relevant correspondence/checking/reporting modules.

## Verification

The final report-boundary test passed:

```text
uv run --locked pytest -q --durations=1 tests/test_correspondence_investigation_reporting.py::test_checked_fin_transport_and_unchecked_application_difference_report_separately
1 passed in 166.60s
```

The focused probe, reviewer-export, identity/fresh-source and investigation
finding suite passed **71 tests in 7.88s**:

```text
uv run --locked pytest -q \
  tests/test_proof_contract_probe_calibration_boundary.py \
  tests/test_proof_contract_probe_calibration_capacity.py \
  tests/test_proof_contract_probe_calibration_controls.py \
  tests/test_proof_contract_probe_calibration_fresh_source.py \
  tests/test_proof_contract_probe_review_cli.py \
  tests/test_investigation_findings.py \
  tests/test_investigation_findings_edges.py \
  tests/test_investigation_findings_pending.py \
  tests/test_correspondence_investigation_v3.py
```

The source correspondence and separate checked counterexample tests also
passed in the first combined run; that run's new report test failed before
semantic assertions because the test helper attached receipt refs after
artifact generation. The helper was corrected to attach refs before building
the checked artifact, and the final report-boundary test passed as recorded
above. This was a test assembly error, not a Lean rejection.

Scoped `scripts/python_quality.py` passed Ruff, Radon, Vulture and maintainability
checks for the investigation/reporting source owners and test. The new test
functions are A/B cyclomatic complexity; the selected existing source owners
are A/B. Python compilation passed. `openspec validate
ladon-proof-contract-probes --strict --no-interactive` passed.

## Exact finite-agreement limitation

Agreement on a finite probe family is only agreement on that family. It implies
equivalence only when accepted checked evidence includes a separating-family
theorem for the exact object class, response/observation function and probe
family being compared. The accepted calibration applies only to the registered
`Fin 5 → Bool` coordinate-evaluation class. It does not establish a separating
family for arbitrary contracts, PDE estimates, or the Navier–Stokes exposition.

The fresh five-family feasibility gate remains limited to constructed
source-bound cases: five local non-implications, five controls and 20 accepted
checker receipts under one 30-minute deadline, with independent PASS. The four
saved v1 templates for constant uniformity, witness dependence, restricted
domain and inequality direction remain unsupported. No natural-language
fidelity, manuscript-error detection, or whole-method claim follows.

## Reporting boundary

`investigation report` validates attached correspondence receipt bindings, but
does not replay Lean and does not copy raw checker receipts into its projected
findings. The checked bundle and refs are preserved alongside the report, whose
formal label remains `recorded-links-only` / `recorded-links-complete-unreplayed`.
An attributed application difference without its own accepted semantic
separation stays distinct and unresolved. This evidence does not demonstrate
that Ladon can detect an error in the Navier–Stokes exposition.
