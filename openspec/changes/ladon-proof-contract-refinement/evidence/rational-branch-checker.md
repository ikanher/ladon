# Bounded rational refinement branch checker

Status: independently audited precursor to task 2.2; task 2.2 remains open.

The new `check_rational_refinement` API in `src/ladon/proof_contract_refinement.py` verifies the existing immutable branch and rechecks all cited source spans, then accepts only expressions with the exact `{op, left, right}` shape supported by `ladon.rational_witness`. It appends all cumulative branch predicates to a deep copy of the supplied base goal, validates the combined goal against the existing rational premise, node, depth, literal and arithmetic limits, and checks the supplied assignment with the exact rational checker.

The `ladon-rational-refinement-check-v1` result binds the branch ID and kind, original finding ID, base and derived goal digests, exact JSON assignment, checker identity and witness check. `checkId` hashes exactly the semantic request object containing the schema, branch ID/kind/finding ID, base and derived goal digests, assignment and checker identity. `resultDigest` hashes every result field except itself. Both use sorted, compact UTF-8 JSON with `ensure_ascii=False` and `allow_nan=False`; keys in mappings are order independent, while equivalent rational spellings such as `1` and `1/1` intentionally remain distinct assignment identities. Verification regenerates and byte-compares the full result, so type changes such as `false` to `0` are rejected.

The checker result is only a status for one assignment against the derived encoded rational goal. It does not certify a translation from source prose to AST, authenticate caller-supplied parent lineage, establish universal truth, connect a branch to ProofIR or Lean checks, or lift/refute an original theorem. `sourceFormulaFidelity` is always `unverified`; `originalClaimRefuted` is always `false`. Proposed-repair branches remain labeled separately and are never evidence for the original claim.

## Verification

- `pytest -q tests/test_rational_refinement_v2.py tests/test_rational_refinement_adversarial_v2.py tests/test_rational_refinement_identity_v5.py tests/test_proof_contract_refinement_branches_v8.py tests/test_proof_contract_refinement_evidence.py tests/test_proof_contract_refinement_json_boundary.py tests/test_proof_contract_refinement_lifting_v2.py` — **39 passed**.
- `python scripts/python_quality.py --target src/ladon/proof_contract_refinement.py --target tests/test_rational_refinement_v2.py --target tests/test_rational_refinement_adversarial_v2.py --target tests/test_rational_refinement_identity_v5.py` — Ruff, Radon, and Vulture passed; all changed functions are Radon A/B and files have A maintainability.
- `python -m compileall -q src/ladon/proof_contract_refinement.py tests/test_rational_refinement_v2.py tests/test_rational_refinement_adversarial_v2.py tests/test_rational_refinement_identity_v5.py` — passed.
- Frozen-test registry verification — passed with zero mismatches.
- Strict OpenSpec validation for this child and its analysis umbrella — passed.
- Independent implementation audit — accepted as board review **#1121** after rerunning the 39-test selection.

This supplies an executable rational-branch semantics seam, but not the semantics-backed ProofIR obligation producer and branch-bound formal receipts required to close task 2.2. It does not change task completion counts.
