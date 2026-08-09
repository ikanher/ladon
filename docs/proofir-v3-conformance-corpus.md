# ProofIR v3 conformance corpus

The shared corpus is intentionally small and reviewable. It is the contract
between the Python reference implementation and the Rust reference crates.
Every fixture is a native ProofIR v3 artifact; unsupported artifact dialects
are rejection cases and are never projected into semantic rows.

The v3.0 canonical numeric profile accepts only integers in the inclusive
interoperable range `[-9007199254740991, 9007199254740991]`. Producers encode
non-integral values as explicitly typed canonical decimal strings. Validators
reject floats and out-of-range integers before hashing, preventing
cross-language byte or precision drift.

| Class | Location | Purpose |
| --- | --- | --- |
| shared valid/invalid corpus | `tests/fixtures/proofir_v3_parity/conformance-corpus-v1.json` | Self-contained canonical bytes, detached IDs, stages, codes, pointers, and messages |
| native envelope vectors | `tests/test_proofir_v3.py`, `rust/proofir-core/tests/python_parity.rs` | Canonical bytes, Unicode, key order, and detached IDs |
| unsupported-input vectors | shared corpus plus `tests/test_proofir_clean_break.py` | Rejection before projection and stable attributable diagnostics |
| attachment vectors | `tests/fixtures/proofir_attachments/resolver-cases-v3.json` | Shared native-v3 attachment decisions, ambiguity, freshness, and unsafe-path behavior |
| SQLite contract | `src/ladon/proofir_sqlite_v3.py`, `tests/test_proofir_sqlite_v3.py` | Constraints, indexes, reconciliation, and access plans |

Diagnostics use the stage, code, pointer, and message stored in the shared
corpus. Adding a case is test-first: add a fixture and a failing assertion
before changing a producer or projection. A semantic change must version the
corpus format or ProofIR contract and update both language implementations;
weakening only one side is not an accepted parity fix.

Release evidence uses the closed
`docs/proofir-v3-release-evidence.schema.json` format. A `ready` release may
contain only requirement rows whose status is `green`; the umbrella closure
gate checks that stronger semantic invariant in addition to JSON Schema shape.

When a producer has stale or unsupported artifacts, regenerate native-v3
artifacts and run native validation before rebuilding disposable projections.
The Rust workspace is deliberately independent of Lean and Quux. Lean
expressions are opaque payloads at the Rust boundary, and no Quux crate,
source path, binary, or test fixture is a dependency.
