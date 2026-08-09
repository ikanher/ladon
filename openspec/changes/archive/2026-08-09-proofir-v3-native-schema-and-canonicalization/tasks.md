## 1. Freeze the native contract

- [x] 1.1 Add valid and invalid v3 fixtures covering every envelope field, supported kind payload, unknown extension, bound, content-ID mismatch, and reference error.
- [x] 1.2 Add canonical byte/hash vectors for key ordering, Unicode, safe-integer boundaries, typed decimal strings, arrays, and extensions.
- [x] 1.3 Freeze stable diagnostic codes, validation stages, JSON pointers, ordering, and retained-artifact behavior.
- [x] 1.4 Add red tests proving every legacy ProofIR kind and the former compatibility kind are rejected and never projected.

## 2. Implement the native artifact layer

- [x] 2.1 Implement the exact common envelope and explicit version-locked validator for every supported kind.
- [x] 2.2 Implement deterministic canonicalization, detached content verification, deep immutable ownership, and safe serialization copies.
- [x] 2.3 Enforce bounded input, output, depth, collection, string, and reference-validation work.
- [x] 2.4 Implement `validate`, `canonicalize`, and `inspect` through the ordinary installed Ladon CLI with atomic output and stable exits.
- [x] 2.5 Remove the converter module/command, compatibility kind, direct legacy dispatch, and legacy adapter projection.

## 3. Verify repeatability and the clean break

- [x] 3.1 Assert repeated validation and canonicalization are byte-identical and source/caller mutation cannot stale an artifact ID.
- [x] 3.2 Assert unknown extensions round-trip but cannot alter core decisions.
- [x] 3.3 Assert native artifacts are the only ProofIR inputs that contribute SQLite rows.
- [x] 3.4 Run native corpus, installed CLI, catalog/projection regression, full Python, and strict quality gates.
