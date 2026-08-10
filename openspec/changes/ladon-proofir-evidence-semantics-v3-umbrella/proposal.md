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
- Harden the alpha architecture against the expert review findings before freezing the semantic contract: authoritative typed validation, distinct declaration/application identities, cross-artifact resolution, a framed Lean worker protocol, portable publication bounds, and reproducible freeze evidence.
- Reopen the four r03 exit classes that were prematurely green: nested payload typing, context-complete application identity, complete artifact/query reference semantics, and ownership-safe SQLite locking.
- Make Lean local context, ordered substitutions, fingerprint schemes, truncation provenance, lock ownership, and packet inventory explicit semantic data rather than implementation conventions.
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
- `proofir-v3-typed-schema-and-corpus-hardening`: One authoritative typed validator, stable Unicode/bound diagnostics, and a complete language-neutral conformance corpus.
- `proofir-v3-declaration-and-application-identity`: Separate declaration, statement, value, and candidate-application identities and prevent residual checks from accepting goals.
- `proofir-v3-cross-artifact-resolution-and-query-contracts`: Resolve incremental external references and make bounded graph/dossier query semantics complete and truthful.
- `proofir-v3-lean-worker-framed-protocol`: Replace source interpolation and first-brace parsing with a nonce-bound framed MetaM protocol.
- `proofir-v3-publication-bounds-and-portability`: Reuse Ladon publication locks, freeze independent resource bounds, and avoid optional SQLite-feature assumptions.
- `proofir-v3-freeze-evidence-and-review-packet`: Produce a content-addressed, packet-local semantic-freeze review boundary and gate Rust on expert-review closure.
- `proofir-v3-rust-reference-core`: Rust implementation of the frozen core contract and conformance suite.

### Modified Capabilities

## Impact

Touches ProofIR cataloging, normalization, bridge adapters, surface/claim/replay/DAG storage, attachment resolution, coverage, theorem dossiers, triage, the Lean semantic-worker boundary, SQLite schema generations and publication, canonical JSON utilities, CLI documentation, fixtures, review packets, and eventually a Rust workspace. The r03 review evidence is authoritative for reopening the affected exit classes. Legacy ProofIR artifacts remain unsupported input, semantic migration is intentionally breaking, database state remains disposable, and Rust stays on hold until a later expert review closes every blocker.
