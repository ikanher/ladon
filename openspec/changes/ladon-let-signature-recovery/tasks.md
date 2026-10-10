# Tasks

Current state: feedback fixes implemented and independently audited; all 20 new cases pass. Installed real-owner replay finds 6 matches instead of 1. Both Python 3.11/3.12 installed populations pass 1,501 contracts each. Full strict qualification is incomplete: the serial retry has 3,308 passed and two unchanged process-cleanup/liveness failures. Task 3.2 remains open for that gate; no assertions or deadlines were weakened. Board `.codex/state/ultra-result-evidence.sqlite3`, topic `lexical-let-fix`. Evidence: `evidence/r01/REPORT.md`, `serial-qualification.json`, and final candidate hashes. Next qualification action: resolve the existing cleanup/liveness issue under its owner, then rerun strict acceptance; no additional signature or runbook changes are pending.

## 1. Preserve supported statement text

- [x] 1.1 RED: freeze CLI/index regressions for consecutive/nested lets, binder defaults, conclusion-only search and proof-body exclusion, with comments/strings and truncation/unsupported controls; verify intended failures on 0.2.2 and retain exact tests.
- [x] 1.2 GREEN/REFACTOR: implement bounded assignment-aware lexical extraction and explicit limitations, document supported scope, and verify frozen tests plus existing lexical/type-text consumers without Lean invocation.

## 2. Recover cached signatures without losing evidence

- [x] 2.1 RED: test recognized prior extractor recovery without source edits, retained-row archival, unknown identity rejection and current no-op byte stability; record actual pre-fix failures.
- [x] 2.2 GREEN: version extraction identity and reuse existing preserved update ownership to re-extract old rows; verify task 2.1, fresh clean lexical parity and existing migration/publication/history contracts.

## 3. Complete the author handoff

- [x] 3.1 Update the matrix-factorization runbook and both relevant Ladon skills, retaining initial/incompatible builds and separate compiled acquisition; verify examples against CLI help and skill validation, preserving concurrent edits.
- [ ] 3.2 Independently audit final sources/tests, replay the reported theorem owners in a disposable index through the ordinary installed CLI, bump to 0.2.3 and run maintained strict plus affected installed contracts on Python 3.11/3.12; record candidate identity and exact outcomes.
- [x] 3.3 Reconcile tasks and feedback dispositions with qualification evidence; verify strict OpenSpec validation and remaining limitations. Preserve prior release evidence; leave commit/archive to explicit request.
