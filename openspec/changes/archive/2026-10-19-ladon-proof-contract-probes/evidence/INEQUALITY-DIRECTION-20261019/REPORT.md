# Inequality-direction v2 source-bound qualification

The fifth typed application-probe family now has a narrow `inequality-direction-v2` consumer. It accepts only the pair `∀ x : Nat, x ≤ 0` and `∀ x : Nat, 0 ≤ x`, with the same binder identity, exact native contract metadata and the allowlisted built-in Nat order context (`object:nat-order`, `domain:Nat`, `scale:none`, `representation:original`). Historical v1 remains unsupported. Custom order contexts, alternate bounds and nearby AST shapes remain unsupported.

On final code, Ladon extracted a complete, premise-free closed application and planned the two original readings against its type. Both plans kept their goals open and claimed no checker or whole-method authority. With one shared 30-minute deadline, 30-second process timeout, 12-GiB RSS cap and 8-MiB output cap, all four Lean goals passed completion, replay and trust in **169.111 seconds**:

- `∀ x, 0 ≤ x` together with `¬ ∀ x, x ≤ 0` checked as `checked-local-nonimplication` for the right-to-left counterexample direction.
- `∀ x, x ≤ 0 → 0 ≤ x` checked as `checked-local-implication` for the left-to-right control direction.
- Both `formal-reading` goals were accepted against the actual extracted source type.

This is a constructed source-bound example, not a natural-language or paper-fidelity result. It does not show that Ladon can find the Navier–Stokes exposition issue, establish prose-to-Lean fidelity, or justify a claim about the complete proof method. The earlier attempts remain preserved under `source-attempt-01/`; they exposed harness selector mistakes and one invalid counterexample term and are not credited.

An independent read-only audit found that equal contracts could previously name a custom order object. The matcher now requires the exact registered Nat order context; regression cases mutate each context field and verify rejection through both the context validator and the probe planner. The reviewer accepted the fix and found no further actionable runtime issue. See [board excerpts](BOARD-EXCERPTS.jsonl).

The focused application-probe regression passed **34/34**. Scoped strict quality and Ruff passed; both relevant OpenSpec changes validate strictly, and all **128** frozen-test records verify. A separate repository-wide strict-quality scan reports an existing C-grade complexity issue in `src/ladon/_proof_contract_probe_domain_contracts.py`; it is outside this inequality-direction change and was not modified here. The complete repository regression was not rerun. Exact inputs, raw goal evidence, extraction, plans, results, resource receipts and failed attempts are retained in the source-attempt directories; `qualify-final.py` reproduces the accepted run using the current checkout.

This completes constructed source-bound discrepancy/control coverage for all five typed families in task 1.1, but the broader five-fault/five-control feasibility gate and all downstream integration tasks remain open. Nothing was pushed.

The saved qualifier accepts a fresh output-directory name, for example `PYTHONPATH=src .venv/bin/python openspec/changes/ladon-proof-contract-probes/evidence/INEQUALITY-DIRECTION-20261019/qualify-final.py source-attempt-06`. Passing `negative-checks` after the directory name also exercises the current source-bound failure and expired-deadline cases described in [checker-negative evidence](../CHECKER-NEGATIVES-20261019/REPORT.md); the completed run is retained as [source attempt 05](source-attempt-05/).

See [validation](VALIDATION.json), [runtime snapshot](runtime.tar.gz), [manifest](MANIFEST.json), and [frozen board excerpts](BOARD-EXCERPTS.jsonl).
