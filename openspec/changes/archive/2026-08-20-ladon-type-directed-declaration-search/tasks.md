## 1. Define The Public Contract

- [x] 1.1 Add `ladon-proof-search-type-result-v1` request/result models with `results`, freshness, coverage, authority, ranking, bounds, omissions, truncation, and nonclaims.
- [x] 1.2 Add `proof-search search type` parsing for module, pattern/file, assumptions, scope, package/namespace filters, candidate/return caps, passes, and freshness.

## 2. Resolve Scope And Build Shortlists

- [x] 2.1 Reuse `proof_search_scope.py` to validate module/import/closure/project/dependency/repository scope and preserve source-only omissions.
- [x] 2.2 Verify repository, index, and worker generation agreement before semantic matching; implement explicit stored-only diagnostic behavior.
- [x] 2.3 Add set-oriented exact-fingerprint, head/arity, shape-prefix, constant-overlap, and semantic-FTS shortlist queries.
- [x] 2.4 Apply scope/ownership/package/namespace filters in SQL, union buckets in priority order, deduplicate by declaration ID, and cap before Lean.

## 3. Verify And Rank Results

- [x] 3.1 Send all shortlisted names through one `check-candidates` request and retain shortlist bucket evidence separately from semantic authority.
- [x] 3.2 Implement the documented lexicographic ranking vector and stable fully qualified name tie-break.
- [x] 3.3 Return verified candidates by default and add an opt-in bounded diagnostic section for rejected shortlist rows.
- [x] 3.4 Add compact text rendering with semantic parity to canonical JSON.

## 4. Test Correctness And Performance

- [x] 4.1 Test exact/wildcard/reducible/symmetry/residual/instance, scope, ownership, namespace, package, stale, cap, and no-match cases.
- [x] 4.2 Assert shortlist statement count is constant and the intended v4 indexes appear in query plans.
- [x] 4.3 Benchmark warm SQLite shortlist, Lean environment load, candidate verification by count, and end-to-end p50/p95 on the reference checkout without rebuilding.

## 5. Verify The Packet

- [x] 5.1 Run installed text/JSON/help contracts, semantic fixture suites, performance/resource gates, compile/quality gates, strict validation, and `git diff --check`.
