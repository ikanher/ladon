## 1. Replace Placeholder Tests With Coverage Matrices

- [ ] 1.1 Add consumer fixtures for missing target, lexical/no dependencies, partial modules, complete empty consumers, complete type/value consumers, ownership filters, and truncation.
- [ ] 1.2 Add constructor fixtures for missing/ambiguous structure, unextracted fields, partial fields, complete zero-field, complete dependent fields, supplied arguments, and leakage classes.
- [ ] 1.3 Mark the current `complete`/`available` placeholder expectations red before editing production handlers.

## 2. Centralize Coverage Evaluation

- [x] 2.1 Implement one read-only semantic coverage evaluator over `evidence_coverage`, module semantic state, selected scope, and actual row populations.
- [x] 2.2 Reject inconsistent metadata/row counts as integrity-unavailable rather than choosing optimistic status.
- [x] 2.3 Return generation, freshness, authority, total/selected populations, omissions, caps, and truncation from the evaluator.

## 3. Correct Consumers

- [x] 3.1 Gate reverse dependency SQL on coverage status and reserve `complete` for a declared complete population.
- [x] 3.2 Preserve indexed type/value/ownership filtering and deterministic bounded ordering.
- [x] 3.3 Add v2 result schema and explicit v1 compatibility/deprecation mapping without reusing misleading semantics.

## 4. Wire Constructor Storage

- [x] 4.1 Replace the empty tuple in `proof_search_cli._dispatch` with read-only structure and ordered field queries.
- [x] 4.2 Resolve exact/module-qualified structure identity and report missing versus ambiguous candidates.
- [x] 4.3 Classify supplied, residual, unavailable, and leakage states only from stored fields plus explicit arguments.
- [x] 4.4 Require explicit complete field coverage before reporting a known zero-field structure.

## 5. Verify Coverage Honesty

- [x] 5.1 Run populated query-plan assertions for dependency target, structure identity, and ordered fields.
- [x] 5.2 Run consumer, constructor, CLI, schema, coverage, deterministic, compatibility, installed-wheel, and full quality suites.
- [x] 5.3 Validate this OpenSpec change strictly and retain nonclaims that empty observations are not Lean proof facts.
