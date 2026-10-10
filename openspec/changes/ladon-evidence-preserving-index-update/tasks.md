# Tasks

Current state: all 17 implementation tasks verified. Ladon 0.2.2 passes 3,290 maintained tests with strict quality checks, 1,481 affected installed contracts on each supported Python runtime, the 13-command fixture/Adam workflow and six per-run preservation/clean-parity measurements. Independent audit 1007 accepts the final candidate. The validated r03 delta packet is `temp/ladon-active-index-review-data-r03.zip`; next: pro review of this bounded maintenance. No automatic refresh or wider product benefit is claimed. Evidence: `evidence/r01/REPORT.md`. Board: `.codex/state/ultra-result-evidence.sqlite3`, topic `index-history`.

Contract: `specs/ladon-index-evidence-history/spec.md`. Architecture and failure semantics: `design.md`. Each RED task precedes its GREEN task; record commands, candidate identity, actual failing assertions and subsequent passing results. Keep test expectations fixed across implementation unless a documented contract correction is independently reviewed. Do not weaken preservation assertions to obtain green.

## 1. Freeze a reproducible evidence-preservation contract

- [x] 1.1 Inventory retained table/column owners and all supported mutation entrypoints; freeze the history CLI/output contract and supported migration layouts. Verify with a source-to-contract inventory, schema-valid fixture inventory and the existing active-index, lifecycle and lineage characterization tests; preserve current known/unknown refusal results before changing expectations.
- [x] 1.2 RED: add public tests for update with mixed semantic/lineage/ProofIR evidence, changed assumptions under the same name, add/remove/rename/import edits, and no-op behavior. Verify intended new cases fail on the current candidate while unknown-layout refusal and existing authority controls pass; retain original refusal assertions as historical evidence with explicit supersession mapping.

## 2. Publish current search while preserving original evidence

- [x] 2.1 RED: add real-SQLite tests for standalone consistent backup, full retained-record equality, separate identities for different evidence under one source generation, archive collision/substitution, and no Lean invocation. Verify failures arise from missing preservation behavior, not malformed fixtures or unavailable imports.
- [x] 2.2 GREEN: implement the bounded feasibility slice with archive/catalog ownership, legacy-layout recognition and a lexical-only active candidate. Verify tests 1.2/2.1 pass and lexical projections equal a clean build; preserve original evidence IDs and values. Stop for design review if this requires rewriting checker/canonical semantics.
- [x] 2.3 REFACTOR: integrate preservation with ordinary `index update`, versioned storage checks and explicit history-size bounds; document its terminal output and disk cost in the index guide. Verify default and explicit index paths, repeated updates, no-op byte stability, retained-history catalog carry-forward and the same red/green assertions.

## 3. Inspect history without promoting it to current evidence

- [x] 3.1 RED: add CLI tests for bounded history listing and exact historical lineage selection without the live project. Cover removed theorems, already-stale closures, text/JSON scope labels, mutation rejection and missing/corrupt/substituted archives; record failures before implementation.
- [x] 3.2 GREEN: implement history selection and owner-bound read-only projection, plus separate lexical/history/current-association status. Verify task 3.1 passes, current queries never borrow old semantic fields and failed new acquisition preserves history without current fallback.
- [x] 3.3 REFACTOR: document and smoke-test the full history-selection recipe from its declared working directory, including external dependency limitations and joint index/history relocation. Verify ordinary current-mode result contracts remain compatible; freeze and document any separately versioned historical wrapper.

## 4. Survive concurrent edits, publication failures and cleanup

- [x] 4.1 RED: add deterministic writer/reader overlap tests and fault injection before/after archive publication and active replacement. Include directory-fsync uncertainty, storage exhaustion, history ceilings and source changes with bounded path diagnostics. Verify failures are behavioral and test barriers do not depend on sleep timing.
- [x] 4.2 GREEN: integrate supported writer locks and failure/recovery handling. Verify no committed evidence is lost, readers observe complete generations, pre-replacement failures retain the old active bytes and post-replacement uncertainty is reported honestly; rerun task 4.1 controls.
- [x] 4.3 RED: add tests for prune protection, rebuild-over-history refusal, unknown evidence extensions, missing history after a partial move, old-reader rejection and orphan inventory. Verify existing protected-file behavior still passes and new lifecycle cases fail as expected.
- [x] 4.4 GREEN/REFACTOR: finish lifecycle/compatibility protections and document recovery, retry and storage behavior. Verify task 4.3 passes, archived bytes remain unchanged, no cleanup widens selection, and no source-capture/completion semantics change as a side effect of update diagnostics.

## 5. Qualify the complete author workflow

- [x] 5.1 Exercise an actual Lean-acquired lineage fixture and a disposable Adam-project copy: acquire evidence, edit sources, update, search, inspect history and acquire new evidence separately. Verify the complete ordinary CLI path, retain every command/output/intervention, and confirm the shared matrix-factorization checkout is untouched. Keep the existing 32 GiB cap and record actual usage.
- [x] 5.2 Measure small and real inputs across repeated ordinary updates, retaining all samples, output identities, wall/CPU time, RSS, extraction counts and active/history/peak temporary disk. Verify lexical parity and evidence preservation for every measured run; report costs without claiming an unmeasured speedup or imposing timing assertions in correctness tests.
- [x] 5.3 Run the integrated maintained strict checks and affected installed index, SQLite publication, lineage, semantic, ProofIR and result-reader contracts on supported Python runtimes. Verify installed origins and candidate hashes, independently audit the final diff against the preservation/authority contract, and resolve concrete findings before acceptance.
- [x] 5.4 Update both Ladon skill copies as applicable and release guidance, bump the package version, and qualify the final versioned distribution with installed contract and documented-workflow checks. Verify skill validation and package/lock/version agreement; preserve unrelated edits and attribute earlier test runs to their actual candidate bytes.
- [x] 5.5 Reconcile the OpenSpec checklist with final evidence and prepare a delta review packet covering the original field need, implementation, red/green records, failure controls, actual costs and remaining limits. Verify source/hash inventory and spec validation; leave unestablished benefits and deferred automatic refresh explicitly open.

## Workflow follow-up

- Commit implementation in coherent reviewed batches when requested; do not archive or publish as a side effect of planning.
- Archive after acceptance using the normal OpenSpec workflow. Reconcile the older unarchived active-index delta without rewriting its historical qualification.
- Automatic refresh, selective compiled reuse and history deletion require separately justified follow-up changes.
