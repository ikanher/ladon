## 1. Freeze the failures first

- [x] 1.1 Add red cases for malformed nested values in environment, claim, derivation, check-run, source-map, attachment, observation, coverage, omission, and extension payloads.
- [x] 1.2 Add Unicode vectors for combining/noncombining forms, controls, non-BMP scalars, and lone surrogates with exact canonical or diagnostic outcomes.
- [x] 1.3 Add independent `maxArtifactBytes`, `maxBatchBytes`, and `maxArtifacts` boundary cases, including many individually valid artifacts that fit the batch cap.
- [x] 1.4 Expand valid/invalid corpus coverage to every artifact kind, cross-artifact reference class, recursive derivation policy, SQLite row family, query projection, truncation, and omission result.

## 2. Make one validator authoritative

- [x] 2.1 Inventory parallel checks in `proofir_v3.py` and typed constructors in `proofir_v3_payloads.py`; write a table mapping each kind to exactly one model constructor.
- [x] 2.2 Replace weaker envelope payload checks with typed-model construction and canonical serialization of that immutable model.
- [x] 2.3 Convert raw Unicode encoding failures and all bound failures into stable ProofIR diagnostics without leaking interpreter exceptions.
- [x] 2.4 Delete superseded parallel validators and coercions; retain bounded namespaced extensions only through their typed extension model. The payload dispatch inventory is now the sole authoritative path; no compatibility coercion remains in the native-v3 boundary.

## 3. Prove the exit class

- [x] 3.1 Run focused payload, canonicalization, mutation, corpus, CLI, and SQLite projection tests.
- [x] 3.2 Verify every registered kind has valid, invalid-type, missing-reference, and projection-or-explicit-nonprojection coverage.
- [x] 3.3 Publish the frozen corpus inventory and exact supported environment-manifest fields; do not lift the Rust hold.

## 4. r03 reopening: make the advertised corpus executable

- [x] 4.1 Import the 25 r03 adversarial payload mutations as language-neutral JSON vectors with expected accepted/rejected status and exact diagnostic stage, code, pointer, and message.
- [x] 4.2 Replace weak nested checks for derivation/plan/attempt/check-run/attachment/governance IDs, enums, policies, summaries, diagnostics, evidence, and rejection reasons with closed typed models.
- [x] 4.3 Reject all 19 unambiguously malformed r03 core values; make explicit reject decisions for path escape, zero coordinates, and end-before-start, then freeze those decisions as vectors.
- [x] 4.4 Require every corpus-inventory row to name at least one executable valid/adversarial vector and fail inventory validation when a named case is absent.
- [x] 4.5 Run every vector through envelope and batch validation and stable diagnostic comparison before projection; retain SQLite nonprojection for invalid vectors.
