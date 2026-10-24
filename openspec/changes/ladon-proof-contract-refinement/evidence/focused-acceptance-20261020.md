# Focused refinement acceptance — 2026-10-20

## Result

The active rational-witness and refinement implementation passes the focused regression selection below: **196 passed**. The selection covers rational search and minimization, the audited shared-deadline session, immutable source-cited and repair branches, conservative lift outcomes, refinement evidence boundaries, claim authority, authority-safe gate/discovery behavior, finding workflows, investigation findings (including capture, edge and pending states), and ProofIR subject-scope revision behavior.

## Exact regression command

```sh
PYTHONPATH=src .venv/bin/python -m pytest -q --durations=10 \
  tests/test_rational_witness_session_v5.py \
  tests/test_rational_witness_search.py \
  tests/test_rational_witness_search_binding.py \
  tests/test_rational_witness_search_subclasses.py \
  tests/test_rational_witness_minimize_v7.py \
  tests/test_proof_contract_refinement_branches_v8.py \
  tests/test_proof_contract_refinement_evidence.py \
  tests/test_proof_contract_refinement_json_boundary.py \
  tests/test_proof_contract_refinement_lifting_v2.py \
  tests/test_proof_contract_authority.py \
  tests/test_authority_safe_gate.py \
  tests/test_authority_safe_discovery_regressions.py \
  tests/test_claim_authority.py \
  tests/test_finding_workflow.py \
  tests/test_findings.py \
  tests/test_investigation_contract_findings.py \
  tests/test_investigation_contract_findings_cli.py \
  tests/test_investigation_findings.py \
  tests/test_investigation_findings_capture_state.py \
  tests/test_investigation_findings_edges.py \
  tests/test_investigation_findings_pending.py \
  tests/test_proofir_v3_subject_scope.py
```

Pytest reported **196 passed in 2.57 seconds** on 2026-10-20. The four superseded session-test drafts are outside the active `tests/` tree under `.codex/state/refinement-budget-red/superseded-tests/`; the active v5 file is registered and its SHA-256 matches the frozen-test registry.

## Applicable quality checks

- `PYTHONPATH=src .venv/bin/python -m compileall -q src/ladon/rational_witness.py tests/test_rational_witness_session_v5.py` — passed.
- `.venv/bin/python scripts/python_quality.py --target src/ladon/rational_witness.py --target tests/test_rational_witness_session_v5.py` — passed scoped Ruff, Radon CC/MI and vulture checks; changed production and active test functions are Radon B or better.
- `openspec validate ladon-proof-contract-refinement --strict` and `openspec validate ladon-proof-contract-analysis-umbrella --strict` — passed.
- Frozen-test registry verification — `verified`, no active hash mismatches.

This is a focused acceptance selection, not a full repository strict-quality or full-suite run.

## Explicit limitations

The suite does not establish source-faithful lifting of rational models, a proof that any model is spurious, source-faithful semantics for arbitrary refinement constraints, branch-aware invalidation in generic context bridges or paired Lean probes, or public CLI integration. Iterative refinement rounds remain unsupported. The source/formal correspondence and Ladon's detection benefit for unfamiliar exposition remain unmeasured. No theorem validity or mathematical falsity claim follows from these regressions.
