## 1. Freeze Candidate And Normalization Cases

- [ ] 1.1 Add binder-bearing theorem fixtures covering explicit/implicit parameters, dependent hypotheses, Unicode/ASCII arrows, qualification, parentheses, unsupported syntax, ambiguity, and true mismatch.
- [ ] 1.2 Add red CLI tests for candidate-name resolution and exact peeled conclusion with residual hypotheses.
- [ ] 1.3 Record current raw-string payloads for compatibility comparison.

## 2. Build Shared Lexical Evidence

- [x] 2.1 Extract or add one versioned lexical type normalization module shared by type search and explain.
- [ ] 2.2 Load a unique declaration, ordered binders, original conclusion, freshness, and authority from the read-only index in one bounded query set.
- [x] 2.3 Implement conservative raw-signature peeling fallback that returns an unsupported boundary instead of guessing.

## 3. Classify Difference Conservatively

- [ ] 3.1 Separate parameter substitutions, matched conclusion, residual premises, mismatches, unsupported syntax, and unresolved identity in the internal result.
- [x] 3.2 Return a lexical-positive classification with residuals when the normalized peeled conclusion matches.
- [x] 3.3 Return `indeterminate-lexical` for parse, ambiguity, unsupported, or normalization uncertainty; reserve negative applicability for established evidence.
- [x] 3.4 Keep one-level suggestions finite, source-linked, freshness-labeled, and explicitly unverified.

## 4. Version And Integrate The CLI

- [x] 4.1 Add a v2 explain result schema with normalization identity, original forms, candidate evidence, residuals, authority, bounds, omissions, and nonclaims.
- [x] 4.2 Wire CLI dispatch to database-aware analysis and retain explicit raw-signature mode.
- [x] 4.3 Add compatibility handling for callers expecting v1 raw comparison.

## 5. Verify Semantic Boundaries

- [x] 5.1 Run positive, residual, negative, indeterminate, ambiguity, stale, suggestion-cap, deterministic, and query-count tests.
- [ ] 5.2 Run type-search equivalence tests proving shared normalization and no implicit Lean invocation.
- [x] 5.3 Run CLI, installed-wheel, schema, full quality, and `git diff --check` gates.
- [x] 5.4 Validate this OpenSpec change strictly and document that lexical applicability is not Lean verification.
