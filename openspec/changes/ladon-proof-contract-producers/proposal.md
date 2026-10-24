# Proposal

## Why

Correct propagation over an inaccurate interpretation still yields an inaccurate audit. Ladon needs independently attributed prose contracts and bounded extraction of supported Lean statement features, with every semantic gap visible.

## What Changes

- Produce prose contracts through source-bound attributed interpretations and preserve alternative readings.
- Extract supported Lean contracts from elaborated statements and selected applications with scoped binder identities.
- Start from statement summaries; expand proof slices only for named unresolved obligations.
- Expose source fidelity and extraction coverage independently and test type-equivalent presentation changes.

The bounded acceptance contract is in [specs/ladon-contract-production/spec.md](specs/ladon-contract-production/spec.md). This is a child of [ladon-proof-contract-analysis-umbrella](../ladon-proof-contract-analysis-umbrella/design.md); dependency order and interface ownership are defined there.

## Capabilities

### New Capabilities

- `ladon-contract-production`: Independent source-bound prose and formal contract production with scoped coverage.

### Modified Capabilities

None. Existing native identity, authority, bounded validation and AND/OR requirements remain in force; this adds a distinct capability without changing their meaning.

## Impact

Reuse correspondence_interpretation.py, proofir_correspondence.py, source-goal capture and lean helpers. New producer adapters and CLI operations depend on the domain child. No unrestricted NLP parser or theorem-name heuristic becomes authoritative.

