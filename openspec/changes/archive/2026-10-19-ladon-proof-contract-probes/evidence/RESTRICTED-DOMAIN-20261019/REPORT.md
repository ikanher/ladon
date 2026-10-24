# Restricted-domain v2 source-bound probe

The new `restricted-domain-v2` consumer passed a bounded source qualification on the endpoint-bound final runtime code. Its deliberately narrow input pair is `∀ x : Nat, P x` and `∀ x : Nat, x ≤ 0 → P x`, with the same typed predicate `P : Nat → Prop`, source binder identity, context, and contract metadata. Each contract's endpoint and conclusion IDs must both equal `predicate:<parsed AST symbol ID>`; other endpoint naming conventions and domain shapes remain unsupported.

The qualification used a constructed Lean declaration with `P x := x = 0` and an extracted closed application of the guarded statement. Ladon planned the original right-side formal-reading equivalence and directional probe with open goals and no checker authority. Under a fresh 30-minute deadline, 12-GiB RSS cap, 30-second per-process timeout and 8-MiB output cap, all four generated goals passed completion, replay and trust in 168.594 seconds:

- `restricted ∧ ¬ unrestricted` was checked as `checked-local-nonimplication`.
- `unrestricted → restricted` was checked as `checked-local-implication`.

The accepted evidence is preserved under [source attempt 04](source-attempt-04/), including extracted source slice, native plans, checked results, raw checker goal records and exact qualification script. The earlier [source attempt 03](source-attempt-03/) and [attempt history](attempt-history/) remain unchanged. The initial pre-refactor checker attempt exposed a replay failure caused by tactic-generated helper references; the successful term-only proofs avoid that replay issue.

The acceptance suite passes 13/13, and related application-probe contract, CLI and memory-stop regressions pass 28/28. Ruff, compileall and repository strict-quality checks pass. Both OpenSpec changes pass strict validation. Frozen-test integrity verifies all 124 registry entries. Independent source-first reviews accepted the exact matcher, early-result scope fix, final refactor and endpoint binding; see [board excerpts](BOARD-EXCERPTS.jsonl). The endpoint review notes the naming rule is conservative and may reject otherwise valid contracts using different IDs. The runtime snapshot is [runtime.tar.gz](runtime.tar.gz).

This is evidence only for the constructed encoded proposition pair. It establishes no natural-language fidelity, arbitrary domain equivalence, target-paper error, or whole-method authority. The broader five-family and five-fault/five-control gates remain open.
