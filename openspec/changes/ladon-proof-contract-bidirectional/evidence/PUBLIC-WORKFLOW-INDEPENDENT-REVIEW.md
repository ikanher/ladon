# Integrated source-workflow audit

Assignment #471. This audit is read-only; no canonical edits and no source CLI / Lean / source-observing tests were run.

## Exact pure verification

Command:

```text
PYTHONPATH=src:tests:tests/support pytest -q tests/test_proof_contract_obligation_check_boundaries.py tests/test_proof_contract_obligation_bundle_truncation.py tests/test_proof_contract_obligation_native.py tests/test_proof_contract_obligation_schema.py tests/test_proof_contract_obligation_validation_worker.py tests/test_proof_contract_obligation_inspect_worker.py
```

Result after root corrections: **22 passed in 0.96s**. The earlier integrated-native pair passed 13/13 in 0.68s, before source workflow refinements.

## Findings and fixes reviewed

- Before root's stop fix, `_check_routes` conflated `state.stopped` with deadline expiry and overwrote the original memory stop reason. Root corrected this at current `proof_contract_obligation_checks.py:83-87`: it now returns immediately if stopped and only sets the deadline message for actual expiry. The #472 resource red packet confirms global attempt count and once-per-route/demand behavior pass; its original memory-stop failure matches this code path.
- Native validation incomplete/memory diagnostic now propagates a stop message and memory report-back boolean at lines 78-84.
- A real path remains for coverage retention on evidence pressure. Root corrected `_run_validated` so a completed validated artifact is decoded and route/demand coverage initialized before saving a compact validation receipt (current lines 67-77). The validation result is already present in `input.json`; `validation.json` is now a receipt with artifact ID plus process supervision data rather than another copy of the whole artifact. This avoids duplicate multi-megabyte artifact persistence and leaves known source demand counts available if the receipt hits the evidence cap.
- Final summary handling now uses `_publish_summary`/`_compact_summary` and `_accounted_summary` to retain a bounded explicit omitted-coverage record and account for the exact saved summary bytes (lines 391-443). The authorized pure tests exercise this accounting. Whole-method authority remains none and mathematical falsity not established.
- Route/source demand coverage is initialized before source construction, records incoming occurrence edges, and processes source check once per `(route,demand)`; global attempt count, monotonic deadline, canonical runner, output/RSS limits, and first resource stop propagate through the loop. Repeated occurrences share the same source check while retaining both incoming edges.
- Source checks are admitted only after `run_obligation_validation` returns completed for the exact native batch; `_validation_plan` resolves artifact/goal and contract owners from the supplied context. Source construction still invokes the exact planned-source binding API with full parent/provider snapshots and selected occurrence identity. Only completed replay acceptance plus trust true marks checked support; all other outcomes remain unresolved.

## Test-contract review at root request

Reviewed `.codex/state/proof-contract-analysis/route-bundle-native/quality-proposal/proposal.patch` (SHA256 `807b176d05a292d8b4c638583bc2df8a505df29db3df15b771ba2f8387e91ecf`). `git apply --check -p0` passes. AST comparison shows exact original assertion multiset retained for the resource test (24 assertions) and evidence-budget test (7 assertions); helper extraction only relocates assertions. New validation-coverage test adds four assertions. Its updated oversized opaque extension uses four separate 1 MiB strings, each within the ProofIR per-string 1 MiB bound, and totals about 4 MiB, within the 8 MiB artifact bound. The prior one-string 4 MiB fixture would have failed before exercising the intended budget condition. The test is a valid synthetic native artifact and the mock validation avoids all source work.

Caveat: after root changed `validation.json` from a full artifact copy to a compact receipt, the 4 MiB new test may no longer force the receipt-save failure path; it still verifies route/source coverage for a large artifact. To prove the stop branch, size the complete input request just below the evidence ceiling (while under the 8 MiB preflight cap) so the receipt fails after native validation, and assert `incomplete` plus retained route/source counts. Root may decide the current positive test is enough for coverage initialization and use the existing summary-budget test for cap behavior.

## Hash ledger

Entry hashes (before root corrections), with unchanged controls preserved in board #473: source checks `c67ed06a569e4dc396fa99a7009849ed0be8c6c166f6445ebbf1095f46338809`; supervision `f4bf09ffcfcf94d3198c0146ab85f5a6388184f0209ff611a531c9cc99f1318e`; native validator `06c8042a82d85f2aafc7333da0b4acdd2ab54fb227788e3fa8e14ded142f3533`; artifact factory `291a38bd39e5da9899001ea2269a72f9d16c693695725218e17c2ded0c76c7dc`; CLI helper `6cb865ee9ae82d2ddc6c3419138a6d09b109b4f55b5ef47bfe8f759cde7fa122`; bundle walk `86ec0a1c08ceca6a705ecffff2691e61eee7f38050fe0716514c3079f0aec51c`.

After root corrections at report time: source checks `fa87925266e5a41e5e6347a0ae8b5b81fb7d0e3d5e1f90c5e733fcd14ae44e1c`; all other production hashes above remained unchanged. Frozen boundaries test hash `6c00830bc3a637a904bfd6739c9eb07dc07b04b66ee75cd7f7a8b3c497ee5fae`.

## Remaining gate

Root owns all canonical changes, frozen test edits, serial source CLI/Lean execution, docs, and final OpenSpec task status. The six named pure tests pass; source CLI tests were not run by this auditor. Re-run only the authorized pure set after any further canonical edit. Preserve serial/source and provider-snapshot boundaries, and treat all source work as local conditional support only.

## Final retained-evidence audit (#482)

This pass was read-only: no tests, CLI, Lean, or source-generation operation was run. All **53** entries in `openspec/changes/ladon-proof-contract-bidirectional/evidence/public-obligations-20261018/MANIFEST.json` match their recorded byte counts and SHA256 values. The evidence copy of `repo/ThreeSteps.lean` and `repo/lean-toolchain` byte-match `tests/fixtures/proof_contract_planned_source/`; the Lean source SHA256 also matches `SUMMARY.json` (`sourceUnchanged: true`). For each of the four saved source wrappers, I rebuilt `requestDigest` from that exact serialized wrapper, its parent/provider snapshots, expected symbols, and the published source prefix; all four match the captured construction record.

The checked run contains 19 files totaling **3,089,710 bytes**, exactly equal to `resourceAccounting.evidenceBytes` in the saved `checked/summary.json`, including `summary.json` itself; the recorded cap is 8,388,608 bytes. Across nested records in both camelCase and snake_case, the greatest measured peak RSS is **3,801,374,720 bytes** (3.54 GiB); none of 72 timeout, memory-limit, or output-limit flags is true. Recorded configured RSS maxima are 12 GiB. The public run report records 126.899610518 seconds against a 180-second budget, four captured source demands, and four captured proof attempts: three completed with accepted replay and trust, and `ThreeSteps.secondBound` rejected on a type mismatch and left unresolved. `ThreeSteps.alternateBound` is checked support on the undescribed route; the described route remains unresolved. The report explicitly leaves domain/conclusion transfer unfinished, mathematical falsity not established, and whole-method authority none. These are fixture-local checked results, not evidence for the full mathematical method.

`RUNTIME.json` and `runtime.tar.gz` agree with the current worktree across all **478** manifest entries. Their SHA256 values are respectively `c075d428e6b9591017647599f5df3390ae099d58974ae37d45c164aa424d93c5` and `d6f85c919f9bf2800915b8c622b2bef3c3c489781485dd1dc0635da913443ab0`.

Final source hashes: `_proof_contract_obligation_check_inputs.py` `f02f8d9c7329e2f86c0a2380f134f69300053d2c22b602065a5a5bc2c8d2d35b`; `_proof_contract_obligation_check_reporting.py` `52c7d87a1223756ea5e5e1ae7903b5d4120d9c819014f69037aa56acc8b923c7`; `proof_contract_obligation_checks.py` `fa87925266e5a41e5e6347a0ae8b5b81fb7d0e3d5e1f90c5e733fcd14ae44e1c`; supervision `f4bf09ffcfcf94d3198c0146ab85f5a6388184f0209ff611a531c9cc99f1318e`; worker `82174ea0bdb1fd11e5bbdd7fea6224846df82c9f07c06128b3fbf8550788b721`; obligation CLI `6cb865ee9ae82d2ddc6c3419138a6d09b109b4f55b5ef47bfe8f759cde7fa122`; bundle `d00937277e2f80bb452661cd610da9602499b748040e2b0cf5356eb981f6a535`; bundle walk `86ec0a1c08ceca6a705ecffff2691e61eee7f38050fe0716514c3079f0aec51c`; artifact factory `291a38bd39e5da9899001ea2269a72f9d16c693695725218e17c2ded0c76c7dc`. This confirms the post-split helper hashes and updates the earlier ledger; semantic review scope and pure-test results above remain as recorded, and are not actual kernel evidence.
