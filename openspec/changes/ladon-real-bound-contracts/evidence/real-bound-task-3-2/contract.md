# Task 3.2 engineering contract

```yaml
parent_objective: OpenSpec ladon-real-bound-contracts, task 3.2
current_target: Add direct comparison and individually admitted propagation for the closed real-bound-v1 profile.
acceptance_contract:
  - Real-bound consumers use their own exact profile dispatch; no Real input is sent through Nat comparison or propagation.
  - A comparison is available only for two exact native Real contract owners whose fresh source and proof evidence is replayed for this invocation.
  - The comparison result states only the relation proved by an actual checked Lean proposition. Context identity includes endpoint, set, parameters, constant scope, and every interpretation obligation; differing contexts stay unresolved unless a separately checked rule explicitly proves their relation.
  - A propagated output is supported only by individually admitted, exact Lean-checked rule applications and exact premise/output owners. Each rule application has fresh evidence; graph connectivity and labels alone cannot derive a Real conclusion.
  - Saved native records/check runs remain historical and cannot be used as fresh authority. Source theorem proof and prose norm bridge remain explicitly unresolved unless directly checked by the operation.
  - Existing Nat profile outputs and meanings remain unchanged. Real-to-Nat fallback is forbidden.
  - Results are closed, bounded, deterministic, and preserve limitations and unresolved states.
change_surface: Real native records/admission/replay; proof contract comparison and propagation; native dispatch and analysis serialization/validation; tests, docs, OpenSpec evidence.
direct_consumers: proof_contract_cli.py; proof_contract_artifacts.py; proof_contract_payloads.py; _proof_contract_payload_analysis.py; proof contract SQLite analysis; propagate_contracts and comparison APIs.
baseline: Dirty multi-change worktree on 2026-10-25; prior Real task 3.1 evidence in evidence/native-admission-20261025/REPORT.md. Existing legacy board .codex/state/ultra-proof-contract.sqlite3.
dependency_policy: No new dependencies. Use current Lean checker and closed ProofIR envelopes. No Nat fallback and no stored-result promotion.
rollback_boundary: Reversible additive profile dispatch and operations; preserve Nat schemas, digests, stored rows, and tests.
resource_contract: Existing 12 GiB RSS cap and finite 600 second admission ceiling; retain bounded input/output/graph caps and supervision.
forbidden_substitutions:
  - Lexical/structural comparison without an actual checked relation proposition.
  - Stored accepted flags or saved historical check receipts as fresh evidence.
  - Inferring equivalence from the same endpoint when any interpretation scope differs.
  - Treating graph edges, rule names, or source declarations as admitted propagation rules.
  - Treating a Real payload as Nat or allowing a Nat evaluator to consume a Real payload.
  - Claiming a paper norm bridge or source theorem proof that the checker did not check.
```

## Baseline source boundaries

- `real_bound_native_record.py` stores endpoint, application, quantifier roles, loss,
  guards, constant binder scope, interpretation, and historical admission receipts.
- `real_bound_native_check.py` currently checks predicate and canonical scalar
  obligations, not the source theorem body or a paper norm bridge.
- `proof_contracts.compare_contracts` and `propagate_contracts` are Nat-profile
  consumers and remain so.
- The old propagation graph validator and evaluator infer only their closed Nat
  rules; their shape is not evidence for Real-bound rule admission.

This contract does not assert that task 3.2 is already implementable end-to-end.
Any unsupported proof obligation must remain unresolved and be recorded as a
specific capability boundary rather than silently converted to a heuristic.
