# Finite rational candidate search

## Accepted slice

Refinement task 1.1 is implemented by `ladon.rational_witness.search_candidates`. It validates a closed rational goal and a finite candidate list for every variable, checks assignments with the existing exact checker, and caps the search at 256 assignments. The result contains the canonical goal and SHA-256 identity, the declared family, attempt trace and per-premise booleans. A false premise is recorded as `outside-assumptions`; a found assignment is only an `abstract-countermodel`; exhaustive survival is `survived-declared-scope`; truncation is `budget-exhausted`.

The goal snapshot used for hashing is also the goal passed to checking. Only built-in JSON containers/scalars are accepted, preventing subclass lookups from making the checked formula differ from the recorded formula. Search order follows the goal variable order and each declared list order. Equivalent duplicate rationals are rejected.

The lift-result helper in `proof_contract_refinement.py` covers only the unsupported case: an incomplete lift preserves the abstract witness and attempt, leaves `originalClaimRefuted` false, provides no spuriousness evidence and keeps the realization-or-incompatibility obligation open. It does not implement a checked lift or proof of incompatibility and does not close task 1.3.

## Verification

- `timeout 30s env PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_rational_witness_search.py tests/test_rational_witness_search_binding.py tests/test_rational_witness_search_subclasses.py tests/test_proof_contract_refinement_lifting_v2.py tests/test_proof_contract_refinement_evidence.py tests/test_proof_contract_refinement_json_boundary.py tests/test_derivation_contract.py tests/test_derivation_workflow.py` — **38 passed**.
- Ruff on the two changed modules and six focused test files — passed.
- `python -m compileall -q src/ladon/rational_witness.py src/ladon/proof_contract_refinement.py` — passed.
- Frozen test registry — **165 records verified**.
- Radon on both changed modules — every function at B10 or better.
- Independent review #1052 accepted the goal-bound finite-search helper. Review #1039 accepted the conservative incomplete-lift projection; it does not certify positive lift or incompatibility cases.
- `python scripts/python_quality.py --strict` remains blocked by the previously recorded `validate_restricted_domain_pair` C14 result in `_proof_contract_probe_domain_contracts.py`. The new functions no longer trigger strict complexity failures.

## Remaining scope

This is local rational-goal search, not natural-language-to-goal translation or source fidelity. It does not establish theorem truth or falsity. Candidate minimization, checked lifting, evidence-supported spuriousness, immutable refinement and repair branches, dependency invalidation, deadline integration, public CLI/report integration and the 30-minute three-outcome feasibility gate remain open.
