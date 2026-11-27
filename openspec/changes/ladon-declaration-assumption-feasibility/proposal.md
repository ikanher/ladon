# Proposal

## Why

Lean accepts both `silly_theorem`, which assumes a natural number equals both zero and one, and `prove_anything`, which assumes a structure whose proof field has type `False`. Both declarations compile without axiom dependencies, and Ladon's ordinary inspection paths gave no finding about their impossible premises.

A review of the first implementation found that an inequality cycle and a parity contradiction were detected, while `P` together with `¬ P` and contradictions inside nested structures were missed. An unrelated data parameter could prevent a finding even with an explicit `False` hypothesis. A user declaration sharing the internal certificate name could prevent replay.

## What Changes

- Add an explicit command that checks the joint assumptions of one compiled theorem. Both user examples shall produce a verified inconsistency finding from their declarations and environments without a supplied refutation.
- Use Lean to construct and refute a closed proposition representing the declaration's premises. Replay must verify the exact premise goal and the refutation's independence from the theorem under review. Report unresolved cases and the reason when the bounded check cannot establish a contradiction.
- Extend the bounded check to elementary propositional reasoning, integer constraints, and facts obtained from nested structures. Retain ordinary data parameters in the joint premise and choose certificate names fresh in the selected environment.
- Reuse projected and derived facts in a bounded Lean proof search so the check can combine arithmetic and logic and handle elementary case analysis and equality.
- Check the five missed cases from the vacuity challenge, including hidden premise aliases, proof dependencies, empty recursive types, strict natural-number descent, and negative integer squares. Give automation an option to fail on inconclusive checks.
- Treat the result as an advisory about the declared hypotheses. Legitimate proofs by contradiction and existing theorem-checking outcomes retain their normal meaning.

This is a declaration-level follow-up to the [feasibility prototype](../ladon-assumption-feasibility/evidence/native-probe/README.md). Its acceptance is scoped by the [new capability](specs/ladon-declaration-assumption-feasibility/spec.md). The broader change owns proof-position context and fixed assignments.

## Capabilities

### New Capabilities

- `ladon-declaration-assumption-feasibility` checks joint assumption consistency for an explicitly selected compiled Lean theorem.

### Modified Capabilities

None.

## Impact

The theorem CLI gains one opt-in command, backed by a pinned Lean worker and its checked refutation evidence. The change affects CLI documentation and focused Lean integration fixtures.
