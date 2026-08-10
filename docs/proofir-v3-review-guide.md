# ProofIR v3 expert review guide

## Review question

Does the current ProofIR v3 umbrella provide a semantically honest,
source-reviewable contract, and are the remaining Lean-worker and freeze-packet
blockers correctly bounded?

## Read in this order

1. `openspec/changes/ladon-proofir-evidence-semantics-v3-umbrella/proof-state.md`
2. `docs/proofir-v3-release-evidence.json`
3. `openspec/changes/ladon-proofir-evidence-semantics-v3-umbrella/design.md`
4. `src/ladon/proofir_v3.py` and `src/ladon/proofir_v3_payloads.py`
5. `src/ladon/proofir_identity.py`, `proofir_attachment_policy.py`, and
   `proofir_v3_queries.py`
6. `src/ladon/semantic_candidate_worker.py` and
   `src/ladon/lean/ladon_semantic_candidate_helper.lean`

## Reproducible focused checks

From a Ladon checkout with the Lean toolchain available:

```text
uv run pytest -q tests/test_proofir_v3_hardening.py \
  tests/test_proofir_v3_corpus_complete.py \
  tests/test_proofir_declaration_application_identity.py \
  tests/test_proofir_incremental_resolution.py \
  tests/test_proofir_query_contracts.py \
  tests/test_proofir_sqlite_native_contract.py \
  tests/test_proofir_sqlite_wave3_contract.py

uv run pytest -q tests/test_semantic_candidate_lean_integration.py \
  tests/test_semantic_candidate_residual_integration.py \
  tests/test_semantic_candidate_worker_v3_contract.py \
  tests/test_semantic_candidate_framed_protocol.py \
  tests/test_semantic_candidate_security_contract.py

uv run --locked python scripts/python_quality.py --strict
openspec validate --all --json
```

## Disposition requested

Please distinguish four claims: typed v3 validation, semantic candidate
observation, SQLite projection/publication, and semantic-freeze readiness.
The packet currently supports the first three only with bounded evidence. It
does not claim theorem truth, packet-local Lean replay, initializer isolation,
or Rust parity. In particular, the helper still enables Lean initializers to
load the target project's compiled environment; this is an explicit open
security/design boundary, not an implicit acceptance.
