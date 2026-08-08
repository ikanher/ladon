## Why

Structure construction needs field-by-field supplier evidence and explicit warnings when a helper merely accepts or projects the certificate it claims to derive.

## What Changes

- Add `proof-search constructor coverage` for instantiated structure fields under explicit modules, parameters, and assumptions.
- Batch field shortlists and Lean checks, preserving direct, premised, stronger-hypothesis, restricted-boundary, unmatched, and unavailable states.
- Detect equivalent-field input and direct/alias projection dependency leakage with exact evidence.

## Capabilities

### New Capabilities

- `ladon-constructor-coverage-and-leakage`: Lean-backed field coverage matrices and authority-separated certificate-leakage diagnostics.

### Modified Capabilities

## Impact

Adds constructor query code, semantic helper operations, coverage/leakage schemas and renderers, structure fixtures, and source-linked tests.
