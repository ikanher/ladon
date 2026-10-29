# Real native consumers and storage inventory (assignment #1646)

Read-only source inventory, 2026-10-25. No builds, tests, or database changes.

## Current native contract path

- `src/ladon/proofir_v3_payloads.py:132-145` dispatches `proofir.contract` to `_validate_contract`; that delegates to `src/ladon/proof_contract_payloads.py:54-85`.
- `validate_contract_payload` is closed over the existing payload keys, requires the exact typed `contract` subject, fixed `PROFILE_DIGEST`, then validates the record through `ladon.proof_contracts.validate_contract`. Statement/conclusion/assumption/source-map/check-run refs are exact typed refs scoped to the envelope subject table/environment; record conclusion and assumption identifiers must agree with reference local IDs. At least one source-map ref is mandatory. Provenance is explicitly non-authoritative (`checkerAuthority=none`, `mathematicalFalsity=not-established`, `fidelity=attributed-unreviewed`).
- `src/ladon/proofir_v3.py` owns supported artifact kinds, canonical envelope IDs, limits, and batch reference resolution. It caps canonical artifact size at 8 MiB and canonical nesting at 64 (`MAX_ARTIFACT_BYTES`, `MAX_DEPTH`); floats are rejected by `_reject_float` (around lines 211-258). Batch validation resolves typed refs against exact owners, so adding a Real variant should continue using these refs and batch validation, not a second resolver.
- Old record semantics are in `src/ladon/proof_contracts.py`; it is a structural validator/comparator for the norm-scale-v1 schema and currently expects that exact closed record shape.

## Consumers that would otherwise accept/interpret contracts

- Comparison, propagation, obligation planning and probe paths are dispatched as `proofir.contract-analysis` stages in `src/ladon/proof_contract_payloads.py`; stage recomputation is in `_proof_contract_payload_analysis.py`. Exact input owners are checked there; propagation recomputes from the native graph/request and source contract records.
- `src/ladon/_contract_propagation_inputs.py:read_contracts` independently validates each envelope, environment and fixed norm-scale profile digest; `proof_contracts` validators are called by propagation and obligation planners. A Real payload therefore needs explicit profile dispatch and an explicit rejection at all old comparison/propagation/obligation/probe entry points until task3.2. Do not let matching `proofir.contract` kind alone admit it.
- `src/ladon/proof_contract_cli.py` has `inspect` plus analysis-specific replay paths, `propagate`, and report publication. `_inspect_native` batch-validates ordinary analysis artifacts; obligations/probes invoke dedicated replay inspectors. Native Real inspection should be a distinct historical/offline view, with no freshness claim unless a fresh check is explicitly run.
- The general envelope reporting path is `proofir.contract-analysis`, not a separate contract report kind; the contract record remains embedded in the native envelope. No specialized projection/report route for an unconsumed contract record was found.

## SQLite projection

- `src/ladon/proof_contract_sqlite.py` defines the normalized disposable projection. Existing `proofir_v3_contracts` already has `profile_digest`, `record_json`, `provenance_json`, exact statement owner/local ID and source pointer; `proofir_v3_contract_sources` normalizes source-map refs. `project_contract` stores canonical record JSON as-is. This is the smallest persistence path for a versioned Real record; no new artifact kind or dedicated table is structurally necessary. Keep discriminator/profile digest in the existing column, and ensure query/report consumers branch/reject by it.
- The schema's profile digest column only checks `sha256:*`, so it does not encode norm-scale-v1 specifically. Contract analyses do have a constrained `stage` enum, so do not route Real artifacts through an existing analysis stage. `proofir_sqlite_v3.py` dispatches projectors by artifact kind and uses explicit disposable rebuild protections for incompatible schema.

## Suggested smallest closed variant and evidence boundary

Keep `proofir.contract` and its existing owning contract subject ID convention. Add a separately versioned Real profile ID/digest and closed Real record validator selected only by that profile; preserve the legacy record validator byte-for-byte/semantically for old digest. Require record and profile digest to agree, reject unknown profile/digest pairs. Keep shared envelope fields, exact statement/conclusion/assumption refs, source-map refs, environment, and check-run refs. The Real payload must bind the actual checked predicate/source snapshot and exact checker/helper identity through check-run/evidence references; JSON booleans, recorded status strings, or detached evidence must never promote authority. Existing artifact IDs remain untouched because no old envelopes are rewritten; new artifacts naturally have content-derived IDs.

Retain `record_json` as canonical JSON for either closed record and `profile_digest` as variant discriminator. This is preferable to a parallel Real table unless query needs demonstrate a concrete indexed access pattern. Use existing typed refs/foreign keys and batch validation for evidence attachment. Do not serialize a Lean `Expr` as an invented JSON AST: the expression is typechecked/replayed in the checker against the exact source/environment and represented natively by existing statement identity plus source/check-run evidence references. This keeps the native representation typed by its owner/ref instead of a lossy untrusted term dump.

The new native tree should remain within ProofIR's depth-64, 8 MiB artifact, collection and string bounds. Existing Real checker outputs/worker receipts can contain process floats; native envelopes cannot. Convert elapsed/deadline values using an existing explicit string/structured receipt encoding (as `proof_contract_obligation_cli._native_receipt` already does), and never put floats in canonical native payloads.

## Open concern

This is a source inventory, not proof that every indirect consumer rejects the Real profile. Before task3.1 acceptance, grep and exercise all ingress paths which call `validate_contract` or inspect `payload.record` directly, especially probes, application obligations, provider expansion, route/context bridges and inspection adapters. Legacy rejection must occur before comparing feature rows or producing derived artifacts.
