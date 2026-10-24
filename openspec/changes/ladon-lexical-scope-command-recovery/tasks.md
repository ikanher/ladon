# Tasks

Current state: **9/9 tasks complete**. Full disposable Mathlib replay reduces missing candidate names from 8,024 to 119 (7,905 recovered); both reported qualified queries and the control return exact CLI matches. The three owner copies recover all 490 previously missing names. All 248 affected contracts, repository Ruff, changed-file strict quality and strict OpenSpec validation pass; distinct audits #1460/#1462 found no material issue. [Qualification and residual limits](evidence/r02/REPORT.md). Extractor v6 retains v5/v4/v3 recovery; source-index algorithm v6 prevents stale module reuse. No full repository strict rerun is claimed, and the separate proof-contract umbrella qualification remains open.

## 1. Freeze regressions

- [x] 1.1 RED: add fixtures and CLI/index regressions for a `noncomputable section … end` inside a namespace, for `@[expose] public section` file heads, `meta section`, compound `end A.B` across section+namespace and section+section, and multi-component `namespace A.B` closed component-wise. Add negative controls: an unknown modifier, a mismatched compound end, and an anonymous section closed by a named end. Verify the intended failures on 0.3.0.
- [x] 1.2 RED: add a name-search regression where an exact-basename row without a candidate name currently yields `exactMatches = 0` alongside `contribution: "exact"`.
- [x] 1.3 Replay private copies of `Mathlib/Analysis/Complex/Exponential.lean`, `Mathlib/Topology/Maps/Basic.lean` and `Mathlib/Algebra/Order/GroupWithZero/Basic.lean` in a disposable index. Record which rows currently lack candidate names.

## 2. Implement scope recognition

- [x] 2.1 GREEN: recognize modifier-prefixed section commands and component-wise namespace/compound-end frames, failing closed on every negative control. Keep the existing comment/string mask and offsets.
- [x] 2.2 Decide the EOF-open rule, record the decision in design.md, and implement it with a test for both mismatch-free and mismatched files.
- [x] 2.3 Align the exact and basename match counters with ranked-row contribution, or rename and document them.

## 3. Recovery and qualification

- [x] 3.1 Advance the lexical extraction identity to v6 and retain v5/v4/v3 update recovery; advance the separate source-index cache algorithm to prevent stale module reuse. Test a no-source-change update on a predecessor index, check that evidence is archived, and check no-op byte stability.
- [x] 3.2 Rebuild a disposable Mathlib companion index and report the null-candidate count before and after. The r01 baseline is 8,024 rows. The prototype estimate of about 136 residual rows is a target, not an acceptance threshold. Confirm that the r01 queries return qualified exact matches.
- [x] 3.3 Run strict OpenSpec validation and the maintained contract suites; record outcomes, including any remaining unresolved-scope classes.
