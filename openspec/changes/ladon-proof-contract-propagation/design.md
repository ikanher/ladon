# Design

## Context

See proposal.md. _proofir_derivation_solver.py performs bounded structural support search with AND premises, OR alternatives and budget-dependent unknowns. Its deterministic first-supported-route semantics must remain unchanged. Quux Propagation.lean supplies a reusable fold pattern, but its ordinary predecessor graph is not itself an AND/OR proof hypergraph.

## Goals / Non-Goals

**Goals:** compute realizable contract alternatives and their explanations over an acyclic supported derivation. **Non-Goals:** declare a global best proof, derive semantic impossibility from an incomplete graph, or treat recurrence cycles as inductive proofs.

## Decisions

### Dedicated evaluator

Add a mathematical evaluator beside the structural solver, reusing validated graph identities and ordered premise occurrences. Evaluate an application only after constructing a compatible combination containing one contract from every premise occurrence. Apply the registered rule and side conditions; record their evidence and substitutions. Alternatives union complete result contracts. Unsupported steps generate residuals; useful checked branches can still be reported without asserting complete alternatives.

Represent route witnesses as shared immutable references rather than copying entire proof trees. Witnesses preserve context, object maps and branch compatibility; local facts from incompatible cases cannot be combined. Repeated premises and shared subproofs retain occurrence identity. Cache only results keyed by graph, rule/profile, context and available evidence; budget-dependent unknown is not a reusable negative fact.

### Antichain reduction

Keep all incomparable contracts up to the declared cap. Prune only when the domain comparator supplies valid dominance evidence for the same endpoint/context and transfer monotonicity justifies substitution in later steps. Do not prune for learned scores or componentwise improvement. Equivalent contracts may share a representative, but retain bounded references to distinct method witnesses and report any omitted provenance.

A route requiring three derivatives and parameter M and another requiring five derivatives without M do not yield a three-derivative M-free route. This generic fixture is a mandatory rejection control, not a target-paper hint.

### Bounds and operational semantics

Use the parent reference, step, depth, frontier and combination limits. Sort by stable IDs for deterministic work order. On a cap, expose the pending statement/step combinations and the exact scope of known results. A complete analysis means complete only over the supplied graph and admitted profile. Cycles return unsupported-cycle with SCC evidence; no fixed-point iteration is admitted in the first version.

Pure graph queries retain the old structural outputs. The new propagate operation emits the contract-analysis propagation variant, with profile digest, selected contracts, route witnesses, pruning certificates and residuals.

## Risks / Trade-offs

- Frontier explosion → cap before materializing a Cartesian product; preserve partial routes and count attempted work.
- Dominance ceases to be valid downstream → admit pruning only for the profile's proved monotone rules.
- Dynamic programming hides lost conjuncts → compare against independent exhaustive enumeration on finite DAGs with at most eight statements and three alternatives per conclusion.
- Antichain research expands into cyclic abstract interpretation → defer cycles; the consuming result is a correct acyclic frontier within a 30-minute oracle suite and parent resource limits.

## Migration Plan

Add a separate operation and payload variant. Keep existing structural solver behavior and regression corpus unchanged. Portable graph tests must run without Quux, Lean installation or a model service; Lean-backed domain calibration is a separate required check.

