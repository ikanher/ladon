# Proposal

## Why

A textual difference may be harmless presentation or a substantive difference in how an estimate can be used. Exact application probes can distinguish contracts and make the suspected mismatch concrete.

## What Changes

- Generate typed probes for regularity, uniformity, quantifier dependence, domain restrictions and inequality direction.
- Check applications and counterexamples in their exact contexts through existing Lean and rational-checker paths.
- Require an explicit separating-family theorem before probe agreement can establish equivalence.
- Retain failed attempts, unsupported probes and ordinary matching controls.

The bounded acceptance contract is in [specs/ladon-contract-probes/spec.md](specs/ladon-contract-probes/spec.md). This is a child of [ladon-proof-contract-analysis-umbrella](../ladon-proof-contract-analysis-umbrella/design.md); dependency order and interface ownership are defined there.

## Capabilities

### New Capabilities

- `ladon-contract-probes`: Evidence-bound application probes that distinguish mathematical contracts.

### Modified Capabilities

None. Existing native identity, authority, bounded validation and AND/OR requirements remain in force; this adds a distinct capability without changing their meaning.

## Impact

New probe planner/runner uses domain, producers and bidirectional obligations plus existing candidate and correspondence execution. Quux ProbeSeparation supplies the bounded design pattern, not a general completeness guarantee.

