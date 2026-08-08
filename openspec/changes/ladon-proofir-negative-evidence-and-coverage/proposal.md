## Why

An empty evidence result currently hides whether ProofIR was unconfigured, unsupported, malformed, stale, unattached, ambiguous, or simply silent about a theorem. Explicit negative evidence is essential for honest LLM and human reasoning.

## What Changes

- Define stored and projected coverage states for catalog, surface, attachment, replay, DAG, witness, and lineage evidence.
- Return structured absence, staleness, ambiguity, and context-only explanations.
- Separate observed absence from unavailable or unconfigured evidence.
- Add deterministic coverage summaries without promoting missing evidence into a theorem claim.

## Capabilities

### New Capabilities

- `ladon-proofir-negative-evidence-and-coverage`: Explicit coverage and negative-evidence semantics across ProofIR projections.

### Modified Capabilities

## Impact

Affects evidence coverage/omission storage, theorem and artifact projections, build/status counts, and negative-oracle tests for Quux and Matrix Factorization.
