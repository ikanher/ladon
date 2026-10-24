# Tasks

Bounded implementation accepted: [acceptance evidence](evidence/ACCEPTANCE.md), [validation and exact file identities](evidence/VALIDATION.json). All eight child gates passed; parent integration and detection-benefit gates remain separate.

## 1. Evaluate complete proof routes

- [x] 1.1 Implement the dedicated bounded AND/OR contract evaluator with ordered premise occurrences and registered rule application; verify missing-conjunct and repeated-premise cases against an independent exhaustive DAG oracle.
- [x] 1.2 Implement route witnesses with branch/context/substitution identity and shared subproof references; verify incompatible cases cannot combine and changed evidence cannot reuse cached support.
- [x] 1.3 Implement complete-contract antichain reduction using admitted dominance and monotonicity evidence; verify the three-versus-five derivative trade-off never produces a fictitious componentwise optimum and document the frontier interpretation.

## 2. Preserve bounded uncertainty

- [x] 2.1 Enforce frontier, combination, node, step, depth and deadline limits before large allocations; verify partial frontiers retain explicit pending work and unknowns do not become cached negatives.
- [x] 2.2 Reject cyclic propagation with cycle/SCC evidence and preserve existing structural solver behavior; verify cycle controls and unchanged structural-query regressions.
- [x] 2.3 Wire propagate/inspect with native analysis artifacts, route/pruning references and completeness fields; verify deterministic replay, malformed evidence rejection and the documented CLI example.

## 3. Deliver propagation evidence

- [x] 3.1 Run the 30-minute finite-DAG oracle gate and domain-backed Lean calibrations; publish exact frontier comparisons, all cap controls and known complexity limitations.
- [x] 3.2 Run focused native graph, context and consumer compatibility checks plus applicable quality checks; publish child acceptance evidence and verify portable tests work without Quux.
