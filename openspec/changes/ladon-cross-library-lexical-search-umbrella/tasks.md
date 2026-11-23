# Tasks

## 1. Find declarations by type fragments

Owner: [Normalized type-fragment search](specs/ladon-normalized-type-fragment-search/spec.md).

- [x] 1.1 Implement the normalized lexical matcher and test equivalent operator spacing, identifier boundaries, stored quoted contents, prime and operator tokens, case, multiple fragments and duplicate fragments in `tests/test_proof_search_type.py`.
- [x] 1.2 Wire indexed conjunction, conclusion-first ranking and per-fragment evidence before result truncation. Test the limit-one case, copied lexical signatures, a genuine conclusion equal to the full type, scope omissions and literal output parity. Exercise Gaussian integral, product integral and dyadic tail-sum shapes with small portable fixtures.
- [x] 1.3 Expose repeatable fragments through standalone and batch options and versioned output. Check standalone/batch argument bounds, validate normalized output under its own schema and replay existing literal v2 and verified batch v1 consumers. Reject empty fragments and mixed query forms. Document both fragment and literal forms in the CLI reference and skill.

## 2. Query a stored index in one batch

Owner: [Stored search batch](specs/ladon-stored-search-batch/spec.md).

- [x] 2.1 Share the per-index query transaction and add the stored branch. Test an explicit detached database, changed source and omitted versus explicit `--repo-root .` from an unrelated directory. Assert zero source captures and one recorded generation across child outputs.
- [x] 2.2 Test stored generation replacement, output bounds and normal verified-mode race and freshness behavior with the existing batch suites. Document the mode, checkout-free example and the distinction between the opened generation and a verified source window.

## 3. Compare results from named libraries

Owner: [Named index search batch](specs/ladon-named-index-search-batch/spec.md).

- [x] 3.1 Implement bounded manifest parsing and path resolution. Test duplicate names, invalid combinations, repository ownership checks, execution limits and resolution relative to the manifest.
- [x] 3.2 Reuse per-index batches to render the ordered aggregate with scoped status, schema and exit handling. Exercise mixed freshness, same-name candidates, different scopes, available-empty and unavailable indexes, one library changing during verification, all unavailable, one oversized group, and aggregate overflow with an existing destination. Verify successful groups remain in the partial JSON response.
- [x] 3.3 Add an agent-ready named-index example using Mf, pinned Mathlib and RH in the CLI reference and skill. Replay the example structure against portable fixture indexes to check paths, commands and output interpretation.

## 4. Verify the integrated search workflow

- [x] 4.1 Run the focused type and batch suites and the installed CLI contract checks. Exercise the same normalized request through standalone, stored batch and a mixed-freshness named batch. Compare per-library results with their independent runs.
- [x] 4.2 Replay the Gaussian, product-integral and dyadic tail-sum examples on the existing RH index read-only, with a two-minute limit per field run. Check that each normalized fragment query returns its expected qualified name and signature-only evidence. Retain queries, index identities, target ranks, truncation, timings and peak memory for the literal, normalized and batch paths. Record any timeout or missing corpus as a field-evidence gap. A field replay requires only supported existing indexes and stays separate from portable CI.

The [field replay](field-replay.json) records the existing database generations, query arguments, target ranks, signature omissions, elapsed time and peak memory. On the named batch, the clean wheel produced the same child queries and results as the development checkout.
