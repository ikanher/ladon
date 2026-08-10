## Why

A Rust implementation becomes useful only after ProofIR has a frozen, small semantic contract and language-neutral conformance corpus.

## What Changes

- Add Rust crates for core types, JSON canonicalization, validation, SQLite projection, and Ladon interop.
- Share the exact v3 conformance corpus and canonical byte/digest fixtures with Python.
- Require cross-language parity for accepted/rejected native artifacts, diagnostics, normalized rows, and database query results.
- Keep Lean-specific expression and checker semantics behind typed opaque references and the Lean worker boundary.

## Capabilities

### New Capabilities
- `proofir-v3-rust-reference-core`: Conformance-gated Rust implementation of the v3 core.

### Modified Capabilities

## Impact

Adds a Rust workspace and build/test dependencies after v3 stabilization. It does not reimplement Lean elaboration or proof checking.
