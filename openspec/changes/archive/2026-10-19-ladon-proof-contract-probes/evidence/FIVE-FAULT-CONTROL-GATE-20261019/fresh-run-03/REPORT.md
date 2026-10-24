# Fresh five-fault/five-control gate

## Result

The current checkout completed all five constructed discrepancy/control pairs
within one shared 1,800-second monotonic deadline. The reconciled run took
1,422.923 seconds (23 minutes 42.923 seconds), including failed harness setup
attempts. The ten selected outcomes contain five checked local
non-implications and five checked local implications. Each has two accepted
Lean goals, for 20 accepted raw checker receipts total. The complete per-goal
bindings, paths and hashes are in [FRESH-RESULT.json](FRESH-RESULT.json).

Each case used a freshly generated source context in a new campaign repository
root. No previous checked-result envelope or checker receipt was supplied to a
fresh check. The verifier checks the common deadline in every request, exact
expected status, complete two-goal coverage, accepted checker receipts,
replay/trust state, proof-term digest, and that every plan still has open goals
with empty `checkRunRefs`.

## Timing and retained attempts

The campaign started with `run_fresh_gate.py`; its absolute deadline was
carried unchanged through later attempts and recorded in each fresh request.
The early attempts are preserved:

- `fresh-run-01` copied old native contexts to a new repository root. Ladon
  rejected the changed source identity before generating any checker goal.
  This is a harness preparation failure, not a semantic result.
- `fresh-run-02` stopped before a probe because the qualification script's
  frozen runtime inventory no longer matched 11 files in the current checkout.
- `fresh-run-03` successfully ran the regularity, uniformity, witness and
  restricted-domain qualifiers, but its wrapper looked for the restricted
  result at the wrong directory. The child returned zero and its complete
  output remained in place. The inequality qualifier then ran separately under
  the original deadline and passed. The reconciliation is recorded as
  `FRESH-RESULT.json`; the intermediate wrapper result remains marked
  incomplete.
- A supplementary witness control first used the reverse implication and
  remained unresolved. That failed term is retained. The selected
  strong-to-weak control was rerun with the correct direction and passed.

The frozen qualification runtime differed from the current checkout in 11
listed files. `constant-uniformity/BASELINE-DRIFT.json` records the original
manifest hash and each changed path's baseline/current hash. The fresh source
qualifier used a copied runtime inventory updated to the current file hashes;
the original inventory was not changed. All fresh source contexts and checker
receipts are from the current checkout.

The four saved v1 template attempts remain explicitly unsupported:
constant uniformity, witness dependence, restricted domain, and inequality
direction. Their result paths and hashes are retained in `FRESH-RESULT.json`.
The v2 matcher profiles remain narrow; this run did not broaden them.

## Verification boundary

These are constructed, source-bound Lean examples. They show local separation
for the specified formula pairs and checked controls for those pairs. They do
not test natural-language fidelity, establish a general separating family,
certify a whole mathematical method, or show that Ladon can detect an error in
the Navier–Stokes exposition or another paper.

## Reproduction and integrity

Run `PYTHONPATH=src .venv/bin/python verify_fresh_gate.py` to read-only
revalidate the ten selected results against the raw receipts. The runner and
source qualifier hashes are recorded in `FRESH-RESULT.json`; the manifest
verifies all fresh outputs, intermediate attempts, report, verifier, runner
scripts, and source qualifiers.
