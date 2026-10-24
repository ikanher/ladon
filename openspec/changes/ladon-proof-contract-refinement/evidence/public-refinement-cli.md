# Public refinement workflow acceptance — 2026-10-22

Task 3.1 and umbrella Task 2.3 are accepted for the bounded Nat/rational profile.
The public CLI now carries a checked spurious model through source-cited
refinement, a separate proposed repair, historical inspection and ordinary
investigation report aggregation. The original finding, rational witness,
native lift result and both branch checks survive unchanged.

The [guide and runnable example](../../../../docs/CONTRACT_REFINEMENT.md) describe
the exact input schema and authority limits. Machine-readable measurements,
artifact identities, source/test hashes and verification commands are in
[public-refinement-cli-results.json](public-refinement-cli-results.json).

## Constructed CLI qualification

Executed from the current Ladon checkout:

```bash
PYTHONPATH=src python scripts/check_refinement_cli.py \
  --output .codex/state/refinement-cli/native-gate-01
```

The script invoked the ordinary `init`, `observe`, `contract refine`, `contract
inspect` and `report --refinement` commands, then checked stale-source rejection.
All stages passed without retry. Total elapsed time was **30.9019 seconds**;
the supervised native worker used **29.8404 seconds** with measured peak RSS
**3,822,260,224 bytes (3.56 GiB)** under its 12 GiB / 120-second caps. All commands
shared the gate deadline; the refinement command applied its earlier timeout.

The selected formal predicate is `n < 2 → n = 0` for natural numbers. Its rational
abstraction admits `-1`. Fresh Lean checking establishes the complete selected
formal mapping and that this value has no natural-number realization, returning
`spurious-countermodel`. The caller's source-cited `x ≥ 0` predicate excludes
that witness; a separate proposed-repair branch `x = 0` also excludes it. Both
rational checks report `outside-assumptions`. The source-cited branch still has
the counterexample `x = 1`, so eliminating the original witness proves no
universal claim. No reference manuscript answers were used.

`contract inspect` and the report preserve the native result as historical
evidence, with `leanReplayed: false` and `liftAuthority: unverified-saved-result`.
They recompute rational checks and verify current sources, but do not authenticate
an imported Lean receipt. A mutated source correctly produced CLI exit code 2.
Report v3 retains the original observation, branch findings, pending work and
clock, adding only refinement evidence and references. Its finding-ID association
is explicitly attributed by ID, without a semantic equivalence claim. Supplements
do not mutate investigation plans or enter finalization receipts.

## Tests and review

- The independent red suite first failed all 14 cases on the missing API, CLI
  and report paths. Root corrected fixture validity before acceptance, then
  extracted quality helpers without changing any of its 51 assertion ASTs.
  Both compared reports use the same explicit fixture clock.
- The 14 frozen contract cases and 19 additional boundary cases pass. Coverage
  includes resource stops, expired deadlines, either branch alone, input
  immutability, source changes during a lift, stale/altered witnesses and branch
  checks, inconsistent resealed artifacts, historical forgery, unsupported
  profiles, duplicate JSON, invalid limits and dangling output symlinks.
- **250 selected regressions passed in 182.62 seconds**, including the existing
  native rational-branch finding/report/final-receipt consumers. The selection
  and JUnit identity are recorded in the JSON evidence.
- Ruff and `strict_quality_issues` pass for the seven changed production modules,
  both new test files and the qualification script. This is scoped qualification;
  the full repository's quality and regression gates remain open.
- Both the child and umbrella pass strict OpenSpec validation.
- Independent integrated source audit **#1321** found no actionable defects.
  The auditor did not run tests or native Lean; the root owns the executed gates.
  Root acceptance is recorded as board **#1322**.

The canonical evidence board remains
`.codex/state/ultra-proof-contract.sqlite3`. Scout #1296 and falsifier #1301
informed contract #1297; the independent red revision is #1309 and green proposal
is #1317. Root integrated the proposal with the input/exit corrections in #1316.
The new frozen tests match. The previously recorded unrelated frozen hash
mismatch in `tests/test_rational_lean_encoder_v2.py` is unchanged; this report
does not claim the whole registry is clean.

## Remaining limits

This accepts one supplied witness and explicit branch predicates. It does not
automatically discover predicates or proof terms, certify prose fidelity, support
general analytic/function-space lifting, or demonstrate unfamiliar-source
detection. It does not establish detection of the Navier–Stokes exposition bug.
The separate multi-round rational session retains its existing bounded scope.
No dependency, database migration, commit, push or archival was performed.
