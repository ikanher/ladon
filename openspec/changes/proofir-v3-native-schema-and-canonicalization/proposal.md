## Why

ProofIR needs one closed native envelope and portable canonical identity instead of adapter-defined dialects.

## What Changes

- Define the exact v3 envelope and closed kind/version dispatch.
- Add bounded canonical JSON, detached IDs, immutable validation, and stable diagnostics.
- Reject legacy and unknown native-looking kinds before projection.

## Capabilities

### New Capabilities
- `proofir-v3-native-schema-and-canonicalization`

### Modified Capabilities

## Impact

Defines the canonical artifact boundary used by CLI validation, SQLite, graph queries, and future parity implementations.
