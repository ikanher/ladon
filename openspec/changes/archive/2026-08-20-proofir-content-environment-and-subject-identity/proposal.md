## Why

ProofIR identities must remain stable across database generations and must not join unrelated local strings.

## What Changes

- Separate canonical artifact, discovery observation, environment, and typed subject identities.
- Scope local references to their owning artifact and exact environment.
- Keep Lean expressions opaque behind versioned fingerprint schemes.

## Capabilities

### New Capabilities
- `proofir-content-environment-and-subject-identity`

### Modified Capabilities

## Impact

Defines the identity model consumed by native-v3 validation, SQLite projection, observations, attachments, and derivations.
