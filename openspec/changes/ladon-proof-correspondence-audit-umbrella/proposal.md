# Proposal

## Why

A Lean proof can establish a theorem while silently repairing its written argument, changing an intermediate claim, or bypassing a definition's existence presupposition. The concrete examples in Bastounis, Circelli and Hansen's [Navier–Stokes lost in translation](https://arxiv.org/abs/2610.08144v1) motivate testing whether Ladon's existing evidence utilities help an auditor substantiate such differences and offer a faithful correction.

## What Changes

- Establish a bounded proof-correspondence audit workflow: preserve a passage and its proposed formal counterpart, identify a disputed statement/definition/inference, check appropriate local obligations, and explain the consequence for the prose.
- Organize three work packages: reproduce the paper's elementary examples and faithful controls; exercise the audit-and-correction recipe with existing tools; audit one pinned published mathematical passage.
- Deliver conventional editable findings, replayable local checks where obtained, attributed correspondence judgments, proposed revisions and precise unresolved questions. A checked final theorem cannot substitute for auditing a questioned intermediate step.
- Make software investment conditional on a concrete missing operation observed during these tasks. Ordinary files plus Lean are a valid completion route; command uptake is not an acceptance criterion.
- Stop after the development cases and one published-passage audit, including a bounded unresolved outcome if support cannot be established. Review the mathematical findings and any specific software contribution separately. The [audit specification](specs/ladon-proof-correspondence-audit/spec.md) owns acceptance requirements.

## Capabilities

### New Capabilities

- `ladon-proof-correspondence-audit`: an evidence-scoped author/auditor workflow for examining the relationship between a proof passage, its definitions and inferences, and a proposed formal counterpart. This is a workflow contract, not a new automatic semantic-verification service or file format.

### Modified Capabilities

None. Existing attachment, checking, claim/guide/assessment, and revision semantics are reused. Their implementation and prior qualification remain independently scoped.

## Impact

- Expected initial outputs are development fixtures, ordinary Lean audit files, audit findings, correction proposals and documentation. No new public command, schema, database, model dependency or backend is presumed.
- Reuse `result_assessments.py`, existing manifest/guide records, `docs/RESULT_EXPOSITION.md`, and the optional source-goal capture/completion route. Local formalization choices and proof-method judgments remain attributable.
- The existing small Lean fixture pins Lean 4.32.1 and has no Mathlib dependency. Reproductions needing Mathlib require an isolated, explicitly pinned environment; they must not silently add Mathlib to the portable suite or require the concurrent matrix-factorization checkout.
- Preserve the previous [result-understanding umbrella](../ladon-result-understanding-and-release-umbrella/tasks.md), its r09 closed cycle and unmet/deferred benefit gate. This change does not reactivate provenance, release profiles, general search, extraction or optimization work.
- Source motivation and the distinction between reported discrepancies and our own observations are recorded in the design. Neither the paper nor an audit establishes Ladon's comparative benefit or certifies human understanding.
