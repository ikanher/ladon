## 1. Capture Current Contracts

- [x] 1.1 Add canonical JSON fixtures for name, index status, lineage route, ProofIR route, text rendering, bounds, omissions, and error exits.
- [x] 1.2 Add semantic predicate helpers that compare public fields without inspecting private SQLite tables.
- [x] 1.3 Add mixed-case exact-name and exact-refinement fixtures and mark only the known assertions as expected failures owned by packet 2.

## 2. Add Measurement Utilities

- [x] 2.1 Add a reusable `sqlite3.Connection.set_trace_callback` statement counter with normalized statement classes.
- [x] 2.2 Add source-checkout and installed-wheel startup timers with cold/warm phase separation.
- [x] 2.3 Record lexical build time, database bytes, peak RSS, name-query time, lineage query time, and ProofIR route time.

## 3. Make Evidence Reproducible

- [x] 3.1 Emit command, commit, repository fingerprint, Python, Lean/Lake, schema, helper, OS, CPU, and timing-run metadata as JSON.
- [x] 3.2 Add one portable command that regenerates baselines without overwriting accepted files unless explicitly requested.
- [x] 3.3 Document which absolute measurements are observational and which semantic predicates are release gates.

## 4. Verify The Packet

- [x] 4.1 Run every baseline fixture twice and assert deterministic semantic output.
- [x] 4.2 Confirm known failures fail for the intended reason and unexpected failures remain fatal.
- [x] 4.3 Run focused tests, compile checks, strict quality, OpenSpec strict validation, and `git diff --check`.
