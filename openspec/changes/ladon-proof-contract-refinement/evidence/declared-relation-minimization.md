# Declared-relation rational witness minimization

## Accepted slice

Task 1.2 adds `minimize_counterexample` to `ladon.rational_witness`. The input assignment must be an exact counterexample to the recorded goal and must use values from each declared ordered rational candidate list. The reduction relation changes one coordinate to its immediate predecessor in that list. Its measure is the sum of coordinate ranks, which strictly decreases for every attempted predecessor.

The minimizer scans variables in goal order and restarts from the first variable after an accepted reduction. Each attempt records the before and proposed assignments, before and after measures, exact checker result and acceptance. `attemptCount` is bounded by 32 by default (and by the explicit cap when supplied); `reductionCount` counts accepted moves. The result reports `locally-irreducible` only after a complete scan accepts no move. If the cap interrupts the search, the current checked counterexample and trace remain available with `minimality: false` and `status: budget-exhausted`.

Minimality means only local irreducibility under this declared immediate-predecessor relation and candidate family. It is not global numeric minimality, source-level evidence, or a theorem claim. The result includes the canonical goal and its SHA-256 identity.

## Verification

- `PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_rational_witness_minimize_v7.py tests/test_rational_witness_search.py tests/test_rational_witness_search_binding.py tests/test_rational_witness_search_subclasses.py tests/test_proof_contract_refinement_lifting_v2.py tests/test_proof_contract_refinement_evidence.py tests/test_proof_contract_refinement_json_boundary.py tests/test_derivation_contract.py tests/test_derivation_workflow.py` — **56 passed**.
- Ruff on the changed implementation and final minimizer regression — passed.
- `python -m compileall -q src/ladon/rational_witness.py` — passed.
- Radon on the changed implementation and final minimizer regression — no function above B.
- Frozen test registry — all active hashes match; superseded red-test revisions are preserved under `.codex/state/refinement-red/minimizer/`.
- Independent audit #1069 accepted the repaired bounded implementation after reproducing and identifying a cumulative attempt-count defect (#1068). The repair returns per-scan deltas, so the cumulative cap is enforced across restarts.
- `python scripts/python_quality.py --strict` still fails only on the previously recorded `validate_restricted_domain_pair` C14 in `src/ladon/_proof_contract_probe_domain_contracts.py`.
- Strict OpenSpec validation passed for this child and `ladon-proof-contract-analysis-umbrella`.

## Remaining scope

This does not implement checked lifting or prove a model spurious; task 1.3 remains open. Shared original-deadline integration, immutable refinements and repair branches, dependency invalidation, public CLI/report integration, the 30-minute lift feasibility gate, full repository verification, and measured detection benefit remain open.
