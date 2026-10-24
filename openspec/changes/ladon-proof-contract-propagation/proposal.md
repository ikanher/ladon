# Proposal

## Why

A proof may offer several routes with different mathematical requirements. Scalar scores or componentwise minima can fabricate a combination that no route establishes, so analysis must retain full alternatives and their conjunctive premises.

## What Changes

- Add a bounded contract evaluator over native AND/OR derivations, separate from the existing structural solver.
- Retain antichains of incomparable complete contracts with replayable route provenance.
- Admit only versioned, supported transfer rules and prune only under certified dominance.
- Report truncation, unsupported cycles and missing rules as residual work rather than global impossibility.

The bounded acceptance contract is in [specs/ladon-contract-propagation/spec.md](specs/ladon-contract-propagation/spec.md). This is a child of [ladon-proof-contract-analysis-umbrella](../ladon-proof-contract-analysis-umbrella/design.md); dependency order and interface ownership are defined there.

## Capabilities

### New Capabilities

- `ladon-contract-propagation`: Bounded route-preserving mathematical contract propagation over derivation hypergraphs.

### Modified Capabilities

None. Existing native identity, authority, bounded validation and AND/OR requirements remain in force; this adds a distinct capability without changing their meaning.

## Impact

New propagation owner reuses proofir_derivation.py indexing and identities without changing existing solver status/selection semantics. Depends on domain; production integration later consumes producers. Quux propagation and antichain examples are design inputs.

