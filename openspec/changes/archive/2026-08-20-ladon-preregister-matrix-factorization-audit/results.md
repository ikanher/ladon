# Results

## Report Paths

- Project JSON: `temp/preregistered-ladon-runs/matrix-factorization/project-mf.json`
- Project text: `temp/preregistered-ladon-runs/matrix-factorization/project-mf.txt`
- Owner JSON: `temp/preregistered-ladon-runs/matrix-factorization/owner-bifr-packed-profile-lean.json`
- Owner text: `temp/preregistered-ladon-runs/matrix-factorization/owner-bifr-packed-profile-lean.txt`
- Packet JSON: `temp/preregistered-ladon-runs/matrix-factorization/owner-bifr-r37-packet.json`
- Packet text: `temp/preregistered-ladon-runs/matrix-factorization/owner-bifr-r37-packet.txt`

## Prediction Comparison

### Project-Level Matrix-Factorization

Status: matched with one useful nuance.

- Predicted acyclic module graph: observed `acyclic: True`.
- Predicted approximately `529` modules: observed `530`.
- Predicted `Mf.lean` is intentionally narrow: observed root-scope pressure
  and `517` modules not reachable from chosen root.
- Predicted top fan-in modules: observed `Mf.DP.Sensitivity` rank `1/530`,
  `Mf.DP.PLDRandomAllocation` rank `2/530`,
  `Mf.DP.ParticipationSetGaussianCore` rank `3/530`, and
  `Mf.DP.GaussianDP` in the top five.
- Predicted top fan-out modules: observed `Mf.NTK`, `Mf.DP.BNB`, and
  `Mf.DP.SGDSensitivityGaussianBridge` in the top three.

Nuance:

- Because `Mf.lean` imports only `Mf.Basic`, Ladon reported
  `Mf -> Mf.Basic` as the only direct root-import closure. That is correct
  for the chosen root and reinforces that namespace-root runs here are
  inventory context, not whole-tree theorem-owner review.

### BIFR Packed-Profile Owner

Status: matched.

- Predicted broad direct import closure through
  `BIFRProductObjectiveHalfSliceLowerWitness`: observed `127` reachable known
  modules and a `root_import_closure_hotspot`.
- Predicted composite import pressure: observed `composite_import_pressure`.
- Predicted declaration-family hotspots: observed `ge_one_add_firstLag`,
  `nonneg`, and `last` as promoted findings, with `rev` and `eq_forward` in
  the family table.
- Predicted proof-family similarity candidates: observed `eq_forward`,
  `ge_one`, `last`, `nonneg`, and `rev` with score `1.0`.
- Predicted shared packed-profile helpers as declaration fan-in kernels:
  observed `bifrHalfLinePackedProfileIndex` rank `1/46`, fan-in `14`.

### r37 Packet Evidence

Status: matched.

- Predicted packet is present: observed `exists: true`.
- Predicted partial, not complete: observed `partial score=3/6`.
- Predicted owner-reference/tests/metadata evidence: observed metadata,
  tests, and owner references passed.
- Predicted witness/checker completeness gaps: observed `witness_json`,
  `checker_script`, and `verification_commands` failed.

## Conclusion

The matrix-factorization run supports the pre-registration. Ladon correctly
surfaces the broad `Mf` inventory context, the BIFR owner’s import/proof-family
pressure, and packet-evidence incompleteness without claiming proof
incorrectness.
