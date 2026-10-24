# Proposal

## Why

An abstract countermodel can reveal either an actual invalid local inference or a constraint lost during interpretation. Ladon needs a bounded, replayable loop that distinguishes these outcomes and preserves each original claim.

## What Changes

- Add exact finite/rational witness search and declared-relation minimization around contract obligations.
- Check witness admissibility and whether an abstract model lifts to the original mathematical context.
- Allow evidence-supported refinement through immutable child revisions without silently strengthening the manuscript claim.
- Preserve budget exhaustion, finite survival and spurious-model outcomes as explicit unresolved evidence.

The bounded acceptance contract is in [specs/ladon-contract-refinement/spec.md](specs/ladon-contract-refinement/spec.md). This is a child of [ladon-proof-contract-analysis-umbrella](../ladon-proof-contract-analysis-umbrella/design.md); dependency order and interface ownership are defined there.

## Capabilities

### New Capabilities

- `ladon-contract-refinement`: Bounded countermodel checking, minimization and evidence-supported abstraction refinement.

### Modified Capabilities

None. Existing native identity, authority, bounded validation and AND/OR requirements remain in force; this adds a distinct capability without changing their meaning.

## Impact

New refinement orchestrator reuses investigation_derivation.py rational checking and existing immutable observations. Depends on domain, producers, bidirectional analysis and probes. No external solver is mandatory and no arbitrary Python evaluation is introduced.

