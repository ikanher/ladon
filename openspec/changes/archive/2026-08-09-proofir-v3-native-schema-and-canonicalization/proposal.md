## Why

ProofIR needs one closed native schema and deterministic identity contract. Ladon is its sole consumer, so retaining obsolete artifact dialects and a converter would add ambiguity without preserving an external compatibility promise.

## What Changes

- Define one common v3 envelope and closed kind-specific payload schemas.
- Define deterministic canonical bytes and detached content IDs.
- Validate bounds, references, diagnostics, and immutable artifact behavior.
- Expose bounded validate, canonicalize, and inspect operations.
- Delete converter behavior and reject every legacy ProofIR kind explicitly.

## Capabilities

### New Capabilities
- `proofir-v3-native-schema-and-canonicalization`: Closed native-v3 interchange, deterministic canonicalization, and strict diagnostics.

### Modified Capabilities

## Impact

Adds native-v3 schemas, canonicalization, validation, CLI contracts, and language-neutral fixtures. Removes legacy conversion and compatibility ingestion. Canonical artifacts remain immutable filesystem objects.
