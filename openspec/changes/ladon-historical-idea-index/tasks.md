# Tasks

## 1. Preservation contract before migration

- [x] 1.1 Freeze the original commit and implement adversarial metric tests first; verify the recorded red run and 12 passing green tests.
- [x] 1.2 Define the historical and preservation contracts; validate the complete OpenSpec packet strictly before schema implementation.

## 2. Persistent historical model and safe migration

- [ ] 2.1 Implement normalized schema and catalogue validation with exact-year/decade, reviewed selection, reference and DAG rejection tests; document the authored format.
- [ ] 2.2 Implement locked, backed-up, measured atomic migration; verify unchanged semantic/lineage evidence and injected failure recovery.
- [ ] 2.3 Preserve proof identities and older snapshot reads; verify before/after stored-query behavior and normal refresh compatibility.

## 3. Usable historical indexing

- [ ] 3.1 Ingest authored catalogues on build/sync and rebind on refresh; verify reproducibility, stale/missing/ambiguous links, and missing-file retention.
- [ ] 3.2 Expose historical projections and CLI operations; verify exact-year, decade and unassessed output and document executable examples.

## 4. Measured acceptance

- [ ] 4.1 Qualify independent backups of an existing real index and semantic fixtures; publish metric coverage, storage/time and query observations with zero preservation loss.
- [ ] 4.2 Run affected regression and quality checks; record acceptance or restore only this task's changes if preservation cannot be achieved.
