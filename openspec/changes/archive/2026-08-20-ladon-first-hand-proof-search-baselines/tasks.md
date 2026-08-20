## 1. Freeze First-Hand Inputs

- [x] 1.1 Add a checked-in manifest containing the report date, Ladon commit, SQLite version, observed Matrix-Factorization counts, database bytes, stored budget, closure identity, and exact commands without copying the live database.
- [x] 1.2 Add deterministic fixture builders for lexical-only, complete-semantic, partial-semantic, known-empty-structure, binder-bearing theorem, populated ProofIR, and two-owner report cases.
- [x] 1.3 Add a high-fan-out lineage fixture whose fingerprinted distribution reproduces a closure-wide recursive edge scan on the supported SQLite version.

## 2. Write Red Contract Tests

- [x] 2.1 Add a consumer test expecting `not-populated` when the target exists but authoritative dependency coverage is absent; verify it fails against current code.
- [x] 2.2 Add constructor tests expecting stored fields and distinguishing unavailable fields from a complete zero-field structure; verify they fail against current CLI dispatch.
- [x] 2.3 Add an explain test whose binder-bearing candidate has an exact peeled conclusion and two residual hypotheses; verify current raw-string comparison fails.
- [x] 2.4 Add conceptual-ranking and owner-projection fixtures with named expected ordering and bounded default sections; verify current behavior fails.

## 3. Capture Plans And Resources

- [x] 3.1 Capture normalized forward/reverse lineage plans and prove the bad plan omits the complete `(closure_id, source|target)` search key.
- [x] 3.2 Capture plans for exact declarations, selected attachments, diagnostics, DAG obligations, stale triage, and foreign-key child operations on populated fixtures.
- [x] 3.3 Record table/index `dbstat` bytes, free pages, row counts, statement counts, elapsed time, output bytes, and deterministic identities in a machine-readable baseline artifact.
- [x] 3.4 Run every baseline twice from fresh processes and fail on deterministic disagreement while retaining both raw timing records.

## 4. Verify Packet Boundaries

- [x] 4.1 Prove the packet changes no production module and requires no sibling repository.
- [x] 4.2 Run the focused baseline suite, schema/integrity checks, deterministic checks, and `git diff --check`; retain expected red tests as named downstream gates.
- [x] 4.3 Validate this OpenSpec change strictly and record the exact downstream owner for every red predicate.
