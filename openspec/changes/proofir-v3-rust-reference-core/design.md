## Context

Rust is desirable for strict types and deterministic tooling, but only after the semantic contract is frozen independently of Python implementation details.

## Goals / Non-Goals

**Goals:** cross-language canonicalization, validation, query projection, and diagnostics parity.

**Non-Goals:** Lean expression parsing, elaboration, theorem proving, or replacing Python before parity.

## Decisions

1. Workspace crates are `proofir-core`, `proofir-json`, `proofir-validate`, `proofir-sqlite`, and `proofir-ladon`.
2. The checked-in corpus and canonical bytes are language-neutral; Rust never shells into Python for semantic decisions.
3. Lean-specific payloads are opaque typed records validated structurally.
4. Every diagnostic code, JSON pointer, digest, and SQLite projection must match Python.
5. CI builds Rust without Quux present; useful Quux algorithms are clean-room reimplementations behind ProofIR-owned APIs.
6. Python remains the reference implementation until parity and performance gates pass.

## Risks / Trade-offs

- [Two implementations drift] → one corpus, differential tests, and versioned canonicalization identity.
- [Premature optimization] → no Rust production switch before complete parity.

## Migration Plan

Land core/json validation first, then SQLite and the Ladon adapter. Switch components independently only after per-crate parity gates.

## Open Questions

- Whether Rust lives in this repository or a separately versioned ProofIR workspace.
