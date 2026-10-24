# Immutable source-cited refinements and proposed repairs

## Accepted slice

Task 2.1 adds `create_refinement_branch` to `ladon.proof_contract_refinement`. It creates deterministic content-addressed branches over an unchanged abstract-countermodel finding. The origin parent ID hashes the complete canonical finding; child parent IDs refer to and verify the content-addressed parent branch. Each branch carries the original finding, discrepancy and witness, the cumulative constraint set, and the additions made in that branch. Constraint IDs must remain unique across the branch.

A source-cited addition must carry a `SourceReader`-verified source path, full-file SHA-256, and exact quoted line span beneath the explicit source root. The result is labeled `source-cited-refinement`; its nonclaims explicitly state that checking the citation does not certify that the supplied expression faithfully formalizes the text. An absent manuscript assumption is represented as a separate `proposed-repair` branch with rationale; it preserves the original discrepancy and cannot count as support for the original claim. A branch cannot mix newly source-cited and repair additions; mixed ancestry is explicitly labeled.

Raw additions are validated against JSON depth, node and byte limits before cloning, then copied through canonical bounded JSON. Extending a prior branch rechecks its identity, original evidence, cumulative constraints and source citations.

## Verification

- `PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_proof_contract_refinement_branches_v8.py tests/test_proof_contract_refinement_lifting_v2.py tests/test_proof_contract_refinement_evidence.py tests/test_proof_contract_refinement_json_boundary.py tests/test_rational_witness_minimize_v7.py tests/test_rational_witness_search.py tests/test_rational_witness_search_binding.py tests/test_rational_witness_search_subclasses.py tests/test_derivation_contract.py tests/test_derivation_workflow.py` — **67 passed**.
- Ruff and compileall passed for both changed implementation modules and focused regression files.
- Radon found no function above B in the changed source and final test files.
- Frozen test registry — all active hashes match; superseded red revisions are preserved under `.codex/state/refinement-red2/`.
- Independent audit #1091 accepted the current implementation and v8 tests. It specifically checked parent identities, ancestry, duplicate IDs, source-root/digest/span validation, repair separation, JSON bounds and nonclaims.
- Strict OpenSpec validation passed for this child and `ladon-proof-contract-analysis-umbrella`.
- `python scripts/python_quality.py --strict` remains blocked only by the previously recorded C14 `validate_restricted_domain_pair` finding in `src/ladon/_proof_contract_probe_domain_contracts.py`.

## Remaining scope

Source-span validation does not certify expression fidelity. No checker-backed original-space lift or incompatibility proof exists, so task 1.3 remains open and the unsupported lift outcome remains the only accepted lift classification. Dependency invalidation (2.2), shared deadline accounting, CLI/report integration and full readiness checks remain open.
