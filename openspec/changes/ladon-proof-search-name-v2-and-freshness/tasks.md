## 1. Centralize Name Normalization

- [x] 1.1 Create or isolate `semantic_name_segments_v1` with fixtures for camel case, acronyms, digits, namespaces, underscores, and Unicode case folding.
- [x] 1.2 Populate `name_casefold` and `name_segments` for every declaration and add the exact B-tree and normalized FTS columns.
- [x] 1.3 Make query parsing call the same segmenter and expose `all`, `any`, `phrase`, and repeatable exclusion requests.

## 2. Implement Name Result V2

- [x] 2.1 Move scoped name querying into `proof_search_name_query.py` and keep `proof_search_query.py` as a thin compatibility wrapper.
- [x] 2.2 Execute exact folded-name lookup first, union it with ranked FTS candidates, deduplicate by declaration ID, and apply stable ownership/FQN ordering.
- [x] 2.3 Emit `results`, `matchMode`, query mode, filters, scope, bounds, omissions, and versioned normalization metadata.
- [x] 2.4 Keep `index query` working for one transition and expose deprecated `rows` only from its compatibility adapter.

## 3. Implement Freshness And Source Coverage

- [x] 3.1 Add `--freshness verify|stored` request validation and make verified mode hash all supported current inputs.
- [x] 3.2 Discover configured source-root files including untracked/unimported owners and record indexed, source-only, unsupported, or omitted status.
- [x] 3.3 Make an explicitly requested existing file with no indexed rows return an omission or error instead of fresh empty success.

## 4. Test Correctness And Access Paths

- [x] 4.1 Convert baseline mixed-case and exact-refinement expected failures into passing monotonicity tests.
- [x] 4.2 Add Boolean-mode, exclusion, ownership, scope, source-only, stale, deterministic-order, and output-cap tests.
- [x] 4.3 Assert exact lookup and FTS queries use intended indexes with no full declaration scan.

## 5. Verify The Packet

- [x] 5.1 Run focused schema/name/status/CLI tests plus installed text/JSON contract tests.
- [x] 5.2 Run compile, strict quality, deterministic fixtures, strict OpenSpec validation, and `git diff --check`.
