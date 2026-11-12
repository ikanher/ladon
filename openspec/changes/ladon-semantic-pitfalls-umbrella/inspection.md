# Planning inspection

Observed 2026-11-09 in /home/codex/projects/ladon. Planning only; no semantic runtime changes or benchmark population has been executed for this umbrella.

## Source and runtime

- User-supplied [pitfalls.tex](../../../temp/pitfalls.tex), SHA-256 `2c6e3850a2e36ab232ca879cb1a1abd467a2962ce8b1c62def71487a676ef0c0`. This local manuscript motivated the categories; its bibliography and philosophical/theoretical claims were not independently audited.
- HEAD at planning inspection: `31df2116ee217e958edb9206afbd5f04e16697f0`. A future baseline must freeze actual runtime bytes, not rely on this planning commit.
- Existing unrelated untracked files `8` and `100000-node` are outside this work.

## Concrete implementation observations

| Area | Inspected evidence | Consequence |
| --- | --- | --- |
| Conditional correspondence | [goal generation](../../../src/ladon/correspondence_check.py) | H → P and H → C → N do not separately establish inhabitance of H. |
| Checked authority | [completion](../../../src/ladon/source_goal_completion.py) | Fresh replay plus the standard axiom allowlist exists; local inconsistent hypotheses are a different issue. |
| Quantifier/representation safeguards | [quantifier test](../../../tests/test_correspondence_quantifier_lean.py), [representation test](../../../tests/test_correspondence_representation.py), [witness scope](../../../tests/test_correspondence_witness_escape.py) | Retain these controls; do not reimplement already tested behavior. |
| Claim integrity and source fidelity | [Lean gate](../../../tests/test_correspondence_lean_gate.py), [fidelity test](../../../tests/test_proof_contract_fidelity.py) | Changed frozen goals and placeholders are guarded; initial interpretation fidelity remains attributed. |
| Premise origins | [provider expansion](../../../src/ladon/proof_contract_provider_expansion.py) | Exact selected providers exist; bounded transitive provenance and source-role diagnostics are additions. |
| Operations and existence | [typed observation guide](../../../docs/REAL_PROSE_OBSERVATION.md), [worked audit cases](../../../docs/PROOF_CORRESPONDENCE_AUDIT.md) | Typing and known-case evidence do not automate existence/property checks. |
| Existing probe families | [template registry](../../../src/ladon/_proof_contract_probe_templates.py) | Regularity, uniformity, witness dependence, domain and inequality profiles exist; preserve their bounded claims. |
| Evaluation | [registration](../../../src/ladon/_contract_evaluation_registration.py) | Hardcoded legacy 24 A / 12 B counts require a separate pitfall profile. |

## Focused prior-turn verification

Command run against this working checkout during the initial question:

```sh
PYTHONPATH=src .venv/bin/python -m pytest -q \
  tests/test_correspondence_m1_red.py \
  tests/test_correspondence_quantifier_lean.py \
  tests/test_correspondence_representation.py \
  tests/test_correspondence_witness_escape.py \
  tests/test_proof_contract_fidelity.py \
  tests/test_correspondence_lean_gate.py
```

Observed result: **7 passed in 397.00 seconds**. This is existing regression evidence reported from the immediately preceding turn, not a frozen comparative baseline or a new execution receipt. New children must freeze their own case/runtime evidence.

## Scope reconciliation

Main specifications for [probe behavior](../../specs/ladon-contract-probes/spec.md), [authority](../../specs/proofir-observation-authority-and-coverage-core/spec.md), and [identity](../../specs/proofir-content-environment-and-subject-identity/spec.md) remain unchanged. This work adds distinct diagnostics and their consumer.

The older [contract evaluation](../ladon-proof-contract-evaluation/tasks.md) and [contract-analysis umbrella](../ladon-proof-contract-analysis-umbrella/tasks.md) retain their open gates. This new small development evaluation cannot close them. Existing product-scope freeze text is historical context; current authorization is to plan these concrete improvements, with implementation starting when the user asks to apply.

