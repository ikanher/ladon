## Why

Bridge and SQLite adapters use different attachment policies, and configuration-declared artifact relationships can drift independently of the evidence they connect.

## What Changes

- Implement one versioned attachment resolver shared by native source-map and SQLite ingestion.
- Prefer explicit environment/declaration identity, then fingerprints, content/range, and bounded fallbacks.
- Retain every candidate and the complete selection decision.
- Represent cross-artifact semantic links as attributable observations over content IDs.
- Treat name-only matches as diagnostics and absent exact witness targets as unbound.

## Capabilities

### New Capabilities
- `proofir-attachment-and-link-observations`: Central source/declaration attachment and artifact-link evidence.

### Modified Capabilities

## Impact

Touches native source attachments, derivation/check-run relationships, repository ProofIR configuration, diagnostics, and SQLite projections.
