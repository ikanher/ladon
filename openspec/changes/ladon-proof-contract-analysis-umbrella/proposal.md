# Proposal

## Why

Ladon can preserve and check selected prose–Lean correspondences, but still relies heavily on an auditor to notice which mathematical contracts differ. Quux's propagation, finite-order and probe experiments suggest a bounded analysis layer that can locate discrepancies while retaining precise evidence and uncertainty.

The target is to help a fresh auditor discover a substantive, source-faithful discrepancy between an exposition and its formalization without an answer-derived location. The Navier–Stokes experiments motivate this work; a known target replay alone cannot establish unfamiliar-source discovery. Development should establish what is reachable through bounded experiments, preserving unsupported and negative outcomes. Passing builds and infrastructure tests establish their own contracts, not this discovery outcome.

## What Changes

- Coordinate seven separately applicable children with explicit interface ownership and dependency gates.
- Expose an opt-in contract audit that combines independently sourced contracts, route-preserving propagation, backward obligations, probes and bounded refinement.
- Keep source fidelity, checked support, route mismatch, mathematical falsity and search coverage distinct in investigation findings.
- Evaluate supplied-contract analysis separately from source interpretation and unfamiliar-source discovery; retain negative results and historical runs.

The bounded acceptance contract is in [specs/ladon-proof-contract-audit/spec.md](specs/ladon-proof-contract-audit/spec.md). Implementation readiness is not evidence of detection improvement.

## Capabilities

### New Capabilities

- `ladon-proof-contract-audit`: Integrated contract-audit workflow and truthful evidence projection across the child capabilities.

### Modified Capabilities

None. Existing native identity, authority, bounded validation and AND/OR requirements remain in force; this adds a distinct capability without changing their meaning.

## Impact

Children own additive Python modules, explicit native ProofIR kinds, selected Lean producers, investigation CLI integration and tests. Existing v3 envelopes, graph semantics, correspondence checks and historical receipts remain authoritative. No Quux import, model-service requirement, automatic paper repair, or new full-paper run is implied by planning.

