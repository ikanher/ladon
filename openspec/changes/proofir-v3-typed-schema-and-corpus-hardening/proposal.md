## Why

The alpha envelope dispatch enforces key shapes but can accept malformed nested values that the immutable payload models reject. The semantic contract cannot freeze while two validators disagree or while Unicode and aggregate-bound failures lack stable diagnostics.

## What Changes

- Make immutable typed payload models the sole validation authority for every registered kind.
- Freeze separate artifact, batch, and artifact-count bounds plus Unicode behavior.
- Expand the language-neutral corpus across every kind, nested field class, reference failure, projection family, and stable diagnostic.

## Capabilities

### New Capabilities
- `proofir-v3-typed-schema-and-corpus-hardening`

### Modified Capabilities

## Impact

Changes native-v3 validation, payload construction, canonicalization diagnostics, corpus fixtures, CLI validation, and the pre-Rust conformance gate. Legacy kinds remain rejected rather than converted.
