## Why

ProofIR currently behaves as a family of useful evidence dialects whose identity, authority, coverage, and graph semantics depend on adapter conventions. Before those conventions are frozen into a new implementation language or a larger database, Ladon needs a smaller proof-evidence core with explicit validation and migration boundaries.

## What Changes

- Remove legacy ProofIR schemas, conversion, direct ingestion, fixtures, and compatibility projections.
- Separate content identity, environment identity, logical subject identity, and generation observation identity.
- Replace overloaded trust/status fields with typed observations, guarantees, authority bases, coverage, and omissions.
- Centralize source/declaration attachment and artifact-link observations under one versioned resolver policy.
- Introduce one closed native-v3 artifact envelope with deterministic canonicalization and diagnostics.
- Replace path-oriented obligation semantics with explicit AND/OR derivation hypergraphs and complete-slice queries.
- Derive a rebuildable SQLite projection from canonical v3 artifacts rather than treating SQLite as the interchange format.
- Integrate v3 evidence into ordinary Ladon CLI surfaces without promoting evidence into theorem truth.
- Implement a conformance-gated Rust reference core only after the native-v3 semantic contract stabilizes.

## Capabilities

### New Capabilities

- `proofir-content-environment-and-subject-identity`: Content, observation, environment, subject, and artifact-scoped local-reference identities.
- `proofir-observation-authority-and-coverage-core`: Typed observations, checker guarantees, authority bases, coverage populations, and limitations.
- `proofir-attachment-and-link-observations`: Central attachment resolution and attributable artifact-link observations.
- `proofir-v3-native-schema-and-canonicalization`: Common native-v3 envelope, kind schemas, canonicalization, strict validation, and stable diagnostics.
- `proofir-derivation-hypergraph-semantics`: Explicit derivation steps, AND premises, OR alternatives, cycles/SCC policy, and proof-slice queries.
- `proofir-v3-sqlite-projection`: Rebuildable normalized SQLite projection and query/access-path contracts.
- `proofir-v3-ladon-integration-and-release`: Ordinary CLI integration, explicit legacy rejection, documentation, calibration, and release gates.
- `proofir-v3-rust-reference-core`: Rust implementation of the frozen core contract and conformance suite.

### Modified Capabilities

## Impact

Touches ProofIR cataloging, normalization, bridge adapters, surface/claim/replay/DAG storage, attachment resolution, coverage, theorem dossiers, triage, SQLite schema generations, canonical JSON utilities, CLI documentation, fixtures, and eventually a Rust workspace. Legacy ProofIR artifacts become unsupported input, semantic migration is intentionally breaking, and database state remains disposable.
