# Answer-informed retest-6 retrospective

Start with [REPORT.md](REPORT.md), then [WORKPLAN.md](WORKPLAN.md).
This is operator/development evidence containing the reference answer. It is not
a fresh audit packet. Exclude it from future blind inputs.

The reference comparison found that both alleged correspondence discrepancies
were already observed in the frozen run. Mathematical falsity was not established.
The immediate proposed improvement is preserving those observations as findings.

Files:

- `cases.json`: two reference discrepancies and six successful local controls,
  with expected separate statement/method/falsity outcomes and historical identities.
- `source-manifest.json`: 31 original file hashes, including frozen findings,
  first reviews, six checked bundles, reference, primary sources and inspected runtime.
- `*-source.txt`, `*-excerpt.txt`: numbered source excerpts for the comparisons.
- `probe_runtime.py`, `runtime-observations.json`: portable public-CLI reproduction
  of authored judgments disappearing from the status summary.
- `test_reporting_contract.py`: proposed future acceptance contract, currently
  two expected failures and one passing control. It is outside `tests/` and does
  not change the frozen acceptance suite or production code.
- `verify.py`, `validation.json`: identity/recorded-label verification and exact
  scope of validation. These do not verify mathematics or replay Lean.
- `test_custody_contract.py`: four passing mutation controls for source bindings,
  selected declarations, observed evidence and unjustified absence claims.

From the Ladon root:

```bash
python3 openspec/changes/ladon-correspondence-field-hardening-umbrella/evidence/retest-6-retrospective/verify.py
.venv/bin/python -m pytest -q openspec/changes/ladon-correspondence-field-hardening-umbrella/evidence/retest-6-retrospective/test_reporting_contract.py
```

The second command intentionally returns 1 on the recorded runtime. The portable
CLI probe uses this checkout's `src` and `.venv`. Source-custody verification
needs the original audit workspace at the paths in the manifest. It fails if a
pinned file changes; never refresh historical hashes to disguise drift.

No rendered artifacts or Lake caches are included; formal excerpts are not a
self-contained Lean project. Existing build evidence is historical only.

For a subsequent review: does this evidence support the broader goal of reliable
NL/Lean correspondence auditing, or only improved reporting? What coherent work
should happen next, with deliverables and stopping criteria? Assess the proposed
direction against that goal; do not infer autonomous mathematical detection from
the portable reporting controls or manufacture a broader benefit claim.
