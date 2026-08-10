## 1. Freeze end-to-end counterexamples

- [x] 1.1 Add one worker check-run plus derivation and one check-run plus residual attempt; require batch projection and ordered incremental projection to produce identical normalized rows.
- [x] 1.2 Add dangling, wrong-kind, stale-ID, and incoming-cycle cases; require atomic rollback and exact diagnostics.
- [x] 1.3 Add graph cases whose topology is local but whose `checkRunRef` is external; require navigation/slice success without treating the check run as a premise.
- [x] 1.4 Add zero, negative, excessive, and boundary query limits plus exact and bounded match-accounting cases.
- [x] 1.5 Add dossier fixtures that expose N+1 access, incomplete step fields, and mislabeled navigation.

## 2. Implement closure and query semantics

- [x] 2.1 Add a typed resolver context over validated persisted artifacts and the incoming batch; run reference validation before any batch row is committed.
- [x] 2.2 Classify reference fields as topology, subject, checker evidence, support, or attachment and validate each against its permitted target kinds.
- [x] 2.3 Permit resolved external non-topological references in single-artifact graph queries while retaining local topology closure.
- [x] 2.4 Validate every public limit as positive and bounded before SQL; define exact versus bounded `matched`, `returned`, `cap`, and `truncated` semantics.
- [x] 2.5 Replace dossier per-subject loops with set-oriented indexed queries and return complete typed derivation-step relationships.
- [x] 2.6 Add or verify production indexes and portable query-plan predicates for the new joins.

## 3. Prove the exit class

- [x] 3.1 Compare normalized rows and query JSON for batch versus each valid incremental order.
- [x] 3.2 Run foreign-key/integrity checks, atomic failure mutations, query-contract tests, query-count regression tests, and plan gates.
- [x] 3.3 Document navigation nonclaims, complete-slice semantics, external evidence treatment, and count precision.

## 4. r03 reopening: complete reference and query integration

- [x] 4.1 Normalize bare check-run input artifact IDs into a typed artifact-reference family and close them against persisted plus incoming artifacts before projection.
- [x] 4.2 Fetch only referenced persisted owners during incremental validation; add dangling, wrong-kind, environment-mismatch, and permitted-unresolved vectors.
- [x] 4.3 Centralize fingerprint schemes in one registry consumed by the Lean worker, artifact builder, SQLite projector, semantic-candidate query, and corpus; freeze worker-to-query matches for every admitted scheme.
- [x] 4.4 Make dependent sections query the complete theorem selector or propagate parent truncation using `matchedAtLeast` and `truncationCause`; never report `matchedExact=true` after an incomplete parent population.
- [x] 4.5 Replace large OR predicates with a portable bounded set relation that stays below SQLite parameter limits, and aggregate premises/substitutions through explicitly ordered subqueries.
- [x] 4.6 Add typed source-map declaration identity fields or an explicit linked evidence artifact so the resolver's strongest tier is representable by valid canonical input.
- [ ] 4.7 Re-run batch/incremental/query JSON parity, query-count, parameter-limit, plan, ordering, and foreign-key gates; retain `partial` until the worker fingerprint query succeeds end to end.
