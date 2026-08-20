## ADDED Requirements

### Requirement: Portable fixtures reproduce the observed failure classes
The baseline suite SHALL contain populated portable SQLite fixtures for a high-fan-out lineage closure, semantic populations that are absent and complete, structures with absent and known-empty fields, binder-bearing theorem signatures, ProofIR dossier and triage rows, conceptual name searches, and a two-owner architecture projection.

#### Scenario: Baseline suite runs without sibling repositories
- **WHEN** CI runs the baseline suite without Matrix-Factorization or Quux
- **THEN** every correctness and query-plan failure class remains reproducible from repository-owned fixtures

### Requirement: Pre-change evidence is captured before production edits
The implementation SHALL record current result payloads, `EXPLAIN QUERY PLAN` rows, SQL statement counts, table/index bytes, warm-query elapsed time, ranking order, and rendered report volume twice before changing production behavior.

#### Scenario: Two baseline runs disagree
- **WHEN** identities, plans, row counts, or deterministic outputs differ between the two runs
- **THEN** the packet remains incomplete and records the discrepancy instead of selecting a convenient run

### Requirement: Baselines distinguish portable gates from observational calibration
Portable fixture predicates SHALL be authoritative release gates; Matrix-Factorization measurements SHALL be fingerprinted observational evidence and MUST NOT make sibling checkout availability a test dependency.

#### Scenario: Matrix-Factorization is unavailable
- **WHEN** observational calibration cannot run
- **THEN** portable acceptance remains runnable and the missing calibration is reported explicitly
