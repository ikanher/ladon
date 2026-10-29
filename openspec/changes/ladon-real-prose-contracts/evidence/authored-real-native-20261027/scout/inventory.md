# Task 2.1 native dispatch/consumer map

Read-only source map against current worktree; no tests/builds/Lean commands run and no production edits made.

## Dispatch and evidence owners

- `src/ladon/proofir_v3_payloads.py:138-145` routes every `proofir.contract` through one profile validator: closed dispatcher boundary.
- `src/ladon/proof_contract_payloads.py:56-64` dispatches only extracted `real-bound-v1` by digest, otherwise Nat `_validate_nat_contract_payload` (`:66-90`). A new authored Real digest currently falls through into Nat and fails digest/record shape. Add explicit authored branch, not extracted Real or Nat validation.
- `src/ladon/real_bound_native_payload.py:15-42,68-119` is the extracted Real model: closed payload, saved provenance restriction, expression fingerprints, exact source anchor, two historical admission check owners. Useful pattern, wrong semantic authority for authored records.
- `src/ladon/proofir_v3.py:387-423` validates bounded batches before projection and calls `_validate_external_references`; `:1073-1108` maps known ref fields to kinds; `:1111-1123` invokes owner recomputation. Authored owner closure must bind exact source-map, interpretation, proposition observation and recognition snapshot/chunk owners. Add kinds/fields only as required and keep every owner batch-closed.
- `src/ladon/proof_contract_payloads.py:249-260` currently dispatches batch ownership only for extracted Real contracts. Add a distinct authored owner validator that checks exact interpretation->source-map, observation/recognition owners, alternativeId/author, typed feature origins, full scopes/guards, and unresolved/unreviewed state. No admission or theorem authority from stored syntax/equality.

## Producer, report and SQLite

- `src/ladon/proof_contract_artifacts.py:144-172` constructor is Nat-only and calls Nat `validate_contract`; new authored producer must be separate.
- `src/ladon/proofir_v3_cli.py:140-163` generic validate/canonicalize/inspect; `:166-175` summary only knows extracted Real. Add explicit authored summary (syntax-only, unresolved, unreviewed, authority none, no truth/falsity claim) if a summary is desired; canonicalize already keeps the full artifact.
- `src/ladon/proof_contract_cli.py:166-201` inspects prose snapshot first, then Real-bound bundle, then native analysis, else verifies Nat prose snapshot. This existing outer-snapshot replay means `produce_prose_contract`/`verify_prose_snapshot` is not an authored Real inspection route. Choose an explicit fresh authored-native inspect path vs historical snapshot replay.
- `src/ladon/proof_contract_sqlite.py:5-12,14-78,106-138`; common dispatch/schema in `src/ladon/proofir_sqlite_v3.py:265-279,1353-1366`. Existing table stores profile digest, exact `record_json`, `provenance_json`, statement/source relation; common artifact table stores canonical full JSON. It does not relationally index check-run refs today. Avoid schema change absent query need; test both canonical artifact and projected record/provenance exact round-trip. Batch validation before projection at `proofir_v3.py:395-422` is rollback boundary.

## Semantic consumers that must reject the new authored profile

- Nat propagation: `src/ladon/_contract_propagation_inputs.py:42-59` explicitly requires Nat digest at `:53`.
- Application probes: `src/ladon/_proof_contract_probe_pair.py:66-79` explicitly requires Nat digest at `:70-71`.
- Comparison/propagation: `src/ladon/proof_contract_payloads.py:269-300,328-342` uses Nat `compare_contracts` and propagation. `src/ladon/_proof_contract_payload_analysis.py:18-44,46-92` specializes analysis only for extracted Real comparison/transfer/chain/coefficient or other named stages. Keep authored Real out until a valid connection consumer exists; report explicit unsupported-profile outcome.
- Uniformity probe: `src/ladon/_proof_contract_probe_uniformity_contracts.py:4,67-70` calls Nat `validate_contract` unconditionally; preserve rejection.
- Provider route: `src/ladon/_proof_contract_planned_source_binding.py:18-59` finds exact provider contract and source maps but has no profile gate. Audit its caller: semantic use of provider['contract'] on the Nat route needs Nat allowlist/reject authored, since source custody alone is not shape compatibility.
- Other native analysis constructors `proof_contract_artifacts.py:8-42,59-138`, `_proof_contract_probe_native.py`, `_proof_contract_obligation_native.py`, `_proof_contract_rational_native.py` consume analyses; keep contract refs profile-gated at semantic entry points.

## Bounded representation risk

Caps are fixed in `src/ladon/proofir_v3.py:25-36`: 8 MiB/artifact, 32 MiB/batch, depth 64, 1 MiB/string, safe integers. Selected exact observation is ~5.4 MB (`openspec/changes/ladon-real-prose-contracts/evidence/prose-shape-v2-20261027/REPORT.md:38-45`); observation renderer can produce depth 128 (`prose-observation-production-20261027/REPORT.md:45`); process receipts include elapsed floats, and ordinary JSON allows finite floats (`src/ladon/proof_contract_source.py:93-122`). Direct embedding can exceed native depth, float-free scalar and single-string limits. Never raise global limits.

Candidate: separate versioned chunk payload with ordered opaque text chunks below 1 MiB, byte/count/hash/snapshot identity, strict chunk assembly and aggregate cap checks. Parse/reconstruct against ordinary observation limits after assembly; keep float history opaque in native envelope. Test reconstruction, reorder/duplication/omission/tamper, deep/oversize/malformed inputs, owner substitution and pre-projection rollback. Alternative: closed typed projection that binds complete proposition digest and every ordered owner; use only if exact reconstruction is not promised. A digest-only stub does not satisfy exact typed owner preservation.

## Minimal integration sequence

1. Freeze closed authored Real schema/profile and honest authority states; reject admission check refs; require alternative/author and owners.
2. Add explicit contract payload + batch-owner dispatch over exact current interpretation/observation/recognition owners; history remains unauthenticated/fresh=false.
3. Add separate artifact producer and choose/test bounded native representation.
4. Add summary/inspection; reuse SQLite schema unless measured query/index need, with canonical+projection round-trip and rollback/rebuild/integrity evidence.
5. Add negative tests for each existing semantic consumer above; connection use comes in Task 2.2.
