## 1. Design from real queries

- [x] 1.1 Capture the v3 dossier, attachment, derivation-slice, alternatives, check-run, coverage, and omission SQL shapes before creating tables.
- [x] 1.2 Add a populated fixture database test that asserts rows retain artifact, observation, environment, and local-reference provenance.
- [x] 1.3 Add failing `EXPLAIN QUERY PLAN` predicates for every equality join, ordered range, recursive seed, and foreign-key lookup used by those queries.

## 2. Build the normalized projection

- [x] 2.1 Add versioned migrations for artifacts, observations, environments, subjects, claims, derivation steps/premises/conclusions/substitutions, check runs/results, surfaces, attachments, coverage, omissions, and extensions.
- [x] 2.2 Add primary keys, unique constraints, foreign keys, enum/check constraints, nullability constraints, and indexes aligned with the captured SQL.
- [x] 2.3 Project only schema-valid semantic rows; retain invalid artifacts and attributable diagnostics without fabricating normalized evidence.
- [x] 2.4 Keep unknown extension payloads isolated and unable to influence core joins, ranking, authority, or coverage.
- [x] 2.5 Make rebuilds transactional, project-local, PID-safe during construction, integrity checked, statistics refreshed, and atomically published.

## 3. Measure and verify

- [x] 3.1 Add row-count reconciliation from canonical artifacts through normalized tables, omissions, and rejected rows.
- [x] 3.2 Add index inventory tests that reject redundant indexes and plan tests that require intended access paths on populated data.
- [x] 3.3 Record database size, build time, warm-query timing, and result-quality baselines on the maintained fixture and a large Lean repository.
- [x] 3.4 Run SQLite schema/access-path/integrity tests and the strict quality gate.
