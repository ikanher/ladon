## Why

Proof search is most useful when it can see the actual local goal and hypotheses.
Users also need a safe way to test a suggested application without modifying the
unfinished production module.

The returned r03 pro review (supplied in the conversation on 2026-10-04) refines
this existing change into the application foundation for proof assistance and
exposition auditing. See the result-understanding umbrella's design decision 10
for the review interpretation and evidence limits.

This child supports the umbrella's [selected AGMAI recommendations](../ladon-result-understanding-and-release-umbrella/sources.md#selected-focus-for-the-current-milestone): precise exposition and explicit informal/formal coverage. Exact application conditions are inputs to auditing a proof step or paragraph; completing this child alone does not establish that exposition outcome.

## What Changes

- Accept a Lean scratch file and line/column and capture the current goal, local
  hypotheses, namespace, open scopes, and imports through the pinned toolchain.
- Map local hypotheses to candidate binders and feed the exact goal/context into
  type search and premise-difference analysis.
- Parse relevant compiler type-mismatch diagnostics into an explicit query input.
- Emit a separate minimal scratch `example` that imports the candidate owner and
  checks a proposed application under supervised Lean execution.
- Keep scratch artifacts outside production source and label failed probes honestly.
- Show instantiated applications and exact residual propositions with their local
  contexts before receipt metadata; residuals do not establish that a goal is false.
- Add explicit application completion against the preserved captured goal, including
  independent compiler replay and a declared placeholder/axiom trust policy.
- Preserve the existing optional scratch behavior for exploration; completion is an
  additive workflow, not a reinterpretation of older acceptance observations.

## Capabilities

### New Capabilities

- `ladon-goal-capture-and-application-probes`: Goal/context extraction, local-binder
  matching, compiler-error queries, and isolated Lean application probes.

### Modified Capabilities

None.

## Impact

- Extends the Lean helper, process supervisor integration, scratch artifact handling,
  CLI location syntax, route cards, and fixtures for incomplete proof owners.
- Reuses the qualified candidate/context and replay owners. It does not replace the
  backend, implement autonomous proving, or require a result manifest to use a lemma.
