## Why

Result dossiers and reading guides currently require separate local evidence paths and a lineage database. A reviewer needs a portable handoff that preserves these inputs and their exact identities while making missing replay dependencies visible.

## What Changes

- Deliver the umbrella's core portable bundle milestone: explicit export selection, deterministic atomic ZIP output, a complete payload inventory, integrity-only verification and safe extraction.
- Allow ordinary `result inspect` and `result guide` to consume a verified bundle outside the original checkout/cache, with stable pagination after relocation.
- Preserve original manifests, canonical evidence, historical reviews and optional predecessor manifests; separate transport paths from canonical identifiers and attributed scholarly identifiers.
- Retain disclosure omissions without collecting excluded files. Core success requires installed offline use on the real fixed-epoch exposition and adversarial archive/reference tests.
- Keep full research-provenance and pinned community-profile integration as later tasks in this child, after their owning umbrella prerequisites. Core completion does not complete this child.

Detailed behavior is owned by [the bundle spec](specs/ladon-result-release-bundles/spec.md) and [parent source mapping](../ladon-result-understanding-and-release-umbrella/sources.md).

## Capabilities

### New Capabilities

- `ladon-result-release-bundles`: Implements the umbrella's planned portable result handoff, integrity verification, disclosure and revision-preservation capability.

### Modified Capabilities

None. Existing result, ProofIR, evidence receipt, lineage and capsule owners retain their authority.

## Impact

Add bundle selection/index schemas and small archive, input, validation and publication modules. Extend the ordinary result CLI and add optional logical lineage references for stable bundle pagination. Use Python's standard library only; no new proof extractor, wire family, runtime dependency, model call, implicit Lean run, network access or repository submission.
