# Final Task 1.1 capture audit

Role: independent custody auditor. Status: **Task 1.1 custody gates met** for the captured runtime; no canonical edits and no large archive writes. No baseline detection/scoring run is claimed.

## Frozen identity and snapshot

- Helper SHA-256: `15eae12c49994ff8231f58ef1fa5b4055c9982242272d805f118616225d962a7`.
- Bundle: `.codex/state/pitfall-runtime/bundles/baseline-v3`.
- Externally pinned manifest identity: `9043c1d61ca611055087474740419a049e5b554ef839ada4b9e30e3b94f2a78d`.
- Manifest SHA matches both this identity and `manifest.sha256`.
- Capture contains 174,981 present rows, 14,816,083,606 uncompressed bytes, and a 5,286,674,379-byte payload.
- Restored root: `/home/codex/.cache/ladon-pitfall-runtime/reconstructed-v3`, outside the donor Git checkout.
- Captured launcher row SHA matches the current reviewed helper.
- Required host loader path and digest are retained in the manifest; selected profile execution checks the host and snapshot loader copies.

## Source/artifact inventory

`source-artifacts-v2.json` and the bundle manifest each retain 13,644 identical pair rows. Every source and artifact path is present in the frozen manifest, all pair digests match corresponding entry digests, and there are no duplicate source or artifact paths. Four unmapped artifacts are explicitly retained with explanations as stale/generated items without a source mapping; they are not silently treated as fresh source pairs.

## Execution and drift evidence

- `reconstruction-v3-r2.json`: identity-bound full verification and 13 terminal commands. Successful checks include preserved Python 3.11 prefix, stdlib/native-extension/Ladon import origins, source-tree Ladon version, both Lean prefixes, both Validation compilations, and final post-drift cleanup verification. Separate negative cases rejected changed Lean source, changed `.olean`, changed Ladon source, changed launcher, and an extra file.
- `lake-relocation-v3-r2.json`: terminal exit 0; both core and Mathlib relocated Lake import roots/Validation checks passed.
- `runtime-consumers-v3.json`: status `passed`; proof-contract and proof-search help ran through the restored runtime and a final identity-bound verify passed.
- Independent red harness rerun: 5/5 passed (11.503s).
- Supplemental results: donor-independent reconstruction, launcher drift, payload corruption, externally pinned identity, changed source with old artifact, and stale pair rejection all passed.
- Resource receipt records 3:09.68 capture, 5.286 GB archive, and measured resident memory. Current filesystem had about 1.03 GB free at audit; this audit added no large files.

## Audit conclusion and limits

Task 1.1's recoverability, import-origin, inventory, and drift gates are met for this pinned x86_64 Linux runtime image. The frozen artifact/source mapping is retained as data; the four unmapped stale/generated artifacts are called out. The historical strict-quality run has 10 pre-existing complexity failures on unchanged files, scoped as unrelated to custody. Task 1.3 execution protocol and baseline/scorer tasks remain separate. No native baseline was run here.

Evidence digests:

- `source-artifacts-v2.json`: `d6ce329748083e772dd4671dba2d9432230f03d918f0e062f5ed2f1ecf89cd17`
- `capture-v3.json`: `e9bc61024a946b73c4be8cfcb67841ae3149ecf066b13c066925e6c05cfb42b5`
- `reconstruction-v3-r2.json`: `dd007bc7751bb76a9f017c9f8cc8e165a99875ef1a34caf8f4d3c43f7cbcb292`
- `lake-relocation-v3-r2.json`: `aa1f398f2c4d50aadf2dc5f3a7f2f1a0d59995f32cf25151bff88b8f529003f3`
- `runtime-consumers-v3.json`: `4376f67d596f3370edb5b3658300c9861ae0d18f970075b25b1535c8b289ef73`
