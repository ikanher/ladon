# Proposal

## Why

String summaries and raw declaration dependencies do not express the regularity, scope and uniformity promised by a mathematical statement. A small typed contract domain is needed before graph propagation can make meaningful, reviewable comparisons.

## What Changes

- Define scoped contracts for a bounded estimate fragment, with regularity, parameter/witness dependence, domain and quantifier information.
- Define denotation, partial dominance and theorem-backed transfer-rule admission, with unknown information preserved.
- Register closed native contract and analysis payloads without changing old artifact identities.
- Provide portable fixtures, checked Lean calibration and explicit unsupported-reader behavior.

The bounded acceptance contract is in [specs/proofir-mathematical-contracts/spec.md](specs/proofir-mathematical-contracts/spec.md). This is a child of [ladon-proof-contract-analysis-umbrella](../ladon-proof-contract-analysis-umbrella/design.md); dependency order and interface ownership are defined there.

## Capabilities

### New Capabilities

- `proofir-mathematical-contracts`: Typed mathematical contract records, transfer rules, partial ordering and evidence identity.

### Modified Capabilities

None. Existing native identity, authority, bounded validation and AND/OR requirements remain in force; this adds a distinct capability without changing their meaning.

## Impact

New contract-domain/validator owners integrate with proofir_v3.py, proofir_v3_payloads.py, reference closure and canonical conformance. This child owns shared schemas used by all later children, not a second Lean kernel.

