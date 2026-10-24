# Proposal

## Why

Passing hand-authored contract examples does not demonstrate discovery in unfamiliar prose, and known-answer replay cannot measure blind detection. The new analysis needs a frozen evaluation that separates those claims and detects regressions in valid controls.

## What Changes

- Freeze separate supplied-contract, source-production and unfamiliar-source evaluation tracks.
- Compare current Ladon and the integrated analyzer under equal inputs, clocks and explicit model/tool configurations.
- Preserve first reports, independent adjudication, false positives, unresolved cases and resource usage.
- Gate broader paper trials on measured results rather than schema completeness or known-answer success.

The bounded acceptance contract is in [specs/ladon-contract-evaluation/spec.md](specs/ladon-contract-evaluation/spec.md). This is a child of [ladon-proof-contract-analysis-umbrella](../ladon-proof-contract-analysis-umbrella/design.md); dependency order and interface ownership are defined there.

## Capabilities

### New Capabilities

- `ladon-contract-evaluation`: Reproducible evaluation of contract analysis, source fidelity and independent discovery.

### Modified Capabilities

None. Existing native identity, authority, bounded validation and AND/OR requirements remain in force; this adds a distinct capability without changing their meaning.

## Impact

New evaluation manifests, portable cases with actual Lean counterparts, CLI-level harness and evidence reports depend on all functional children. Protocol and held-out custody can be prepared early; execution requires the frozen integrated runtime. Existing retest directories and handoffs are preserved.

