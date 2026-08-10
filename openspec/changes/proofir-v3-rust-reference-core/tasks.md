## 1. Gate the port on frozen vectors

- [ ] 1.1 Confirm the v3 schemas, canonical vectors, invalid corpus, diagnostics, and SQLite projection contract are versioned and frozen before creating Rust production code.
- [ ] 1.2 Create parity tests that execute Python and Rust on the same corpus and compare canonical bytes, IDs, validation stages, diagnostics, and normalized rows.
- [ ] 1.3 Add a CI job that runs with neither Lean nor Quux installed and requires all core Rust tests to pass.

## 2. Implement the reference crates

- [x] 2.1 Create crates for core types, JSON/canonicalization, validation, SQLite projection contract, Ladon adapters, and the Lean-client boundary.
- [ ] 2.2 Implement bounded parsing, strict version dispatch, typed references, observations, coverage, derivations, omissions, and extensions from the frozen schemas.
- [ ] 2.3 Treat Lean expressions and checker guarantees as opaque typed payloads; do not implement Lean elaboration, definitional equality, or instance synthesis in Rust.
- [ ] 2.4 Implement the normalized SQLite projection contract with artifact-scoped identities, constraints, foreign-key indexes, query-plan gates, integrity checks, and accounting parity.
- [x] 2.5 Independently implement required generic algorithms in owned crates; add no Quux import, linkage, invocation, vendoring, or test dependency.

## 3. Prove parity and adopt safely

- [ ] 3.1 Resolve every parity difference by changing an implementation or explicitly versioning the shared contract, never by weakening one side's tests.
- [ ] 3.2 Benchmark canonicalization, validation, projection, and bounded graph queries against the Python reference on fixed corpora.
- [ ] 3.3 Add differential fuzz/property tests for malformed data, bound handling, reference closure, and deterministic diagnostics.
- [ ] 3.4 Document deployment, fallback, clean-break, and operational rollback boundaries before any production switch; do not add legacy schema compatibility.
- [ ] 3.5 Run the full cross-language conformance, Clippy/format/test, Python regression, and no-Quux dependency gates.
