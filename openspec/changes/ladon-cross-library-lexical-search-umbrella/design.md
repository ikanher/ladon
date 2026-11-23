# Design

## Context

The repository-scope RH replay used eight queries on installed Ladon 0.4.4. The verified batch took 27.6 seconds in that run. Separate earlier batches over the RH, Mathlib and Mf indexes each returned their own generation and freshness evidence. The 0.5.0 checkout has the same search options. The behavior changes are defined in the three delta specs.

The current `proof_search_type.py` executes case-folded literal substring predicates on `type_text`, `rendered_type` and `conclusion_text`. It orders by type status and name before applying limits. The lexical writer copies the signature, including binders, into all three columns. On the existing RH snapshot all three replay targets have this layout and carry `lexical-signature` status. For example, `AEMeasurable` occurs in the product-integral hypothesis. A hit in its copied `conclusion_text` column gives no evidence about the conclusion. The name path has a separate token-ranking contract. The current `proof_search_batch.py` runs parsed name/type queries inside a read-only transaction, compares two source snapshots and checks the active index generation before returning verified rows. It already has query and serialized-byte bounds and failure rendering.

## Goals / Non-Goals

Enable local lexical discovery with independently versioned match and freshness evidence. Keep dependency direction from the pure query to the per-index read operation and then to aggregation. The existing Lean candidate checker remains the authority for an application.

The work is scoped to deterministic lexical discovery using existing indexes. Embedding retrieval, elaborated unification and automatic import selection remain in their existing project scopes.

## Decisions

### 1. Add a separate normalized fragment form to type-text search

Use repeatable `--fragment TEXT` options as an alternative to the existing `--pattern TEXT`. Apply the same parser and argument bounds in standalone and batch mode. Examples:

```sh
ladon proof-search search type-text --repo-root "$RH_SRC" \
  --fragment '‖y-a‖^2' --fragment '(s * c / (s + c))'
ladon proof-search search type-text --repo-root "$RH_SRC" \
  --fragment '∫⁻' --fragment 'Measure.pi' --fragment '∏'
```

Use a small documented lexical tokenizer over stored type strings and query fragments. Match contiguous token sequences and keep token boundaries and quoted contents. Compare token spelling case-sensitively. Preserve identifier primes, distinguish a contiguous operator such as `:=` from the tokens `: =`, and preserve quoted contents as stored. The lexical writer already folds source whitespace, including inside literals, so source-exact quote matching is unavailable on those rows. Reject empty or whitespace-only fragments and mixed pattern/fragment requests. Treat normalized duplicates as one fragment. Use versioned ranking by distinct conclusion matches, type status and the existing stable name/module/line/ID ordering. Credit a conclusion match only when extraction provenance identifies the field as a separate conclusion. A lexical fallback contributes signature evidence once and scores zero for conclusion matches. Column equality alone cannot decide provenance since a genuinely extracted conclusion can equal the whole type. Each fragment must fit within a single eligible field, but different fragments may match different fields on one declaration. Return the contributing fields and conclusion availability. Give normalized results a separate schema identifier. The literal v2 schema fixes both the matching policy and the required query pattern. Keep literal v2 and the existing verified name/literal batch v1 contract for existing invocations.

Reuse existing index columns and scope predicates. An initial implementation can evaluate token matches in the read query and apply the bounded shortlist after ranking, with no mandatory index rebuild. Existing FTS may narrow candidates only where its tokenizer and query form are demonstrably recall-preserving for the selected fragment. A first-N literal shortlist can lose a stronger candidate that needs normalization or occurs later in the index, so ranking and truncation must be applied to the complete lexical match population within the selected scope. Avoid materializing every matching row in Python.

### 2. Give the batch reader an explicit stored mode

Use `search batch --freshness stored` alongside the current default `verify`. Parse and bound requests once and share the read-only transaction and child-query code. In stored mode the opened SQLite snapshot supplies the generation and recorded origin. Support an explicit database with no checked-out source. If the caller also supplies a repository as the asserted owner, check it against metadata. Preserve whether `--repo-root` was supplied at batch argument parsing. Its current default of `.` erases that distinction before dispatch. With only `--index` in stored mode, use the recorded owner for provenance even when invoked from another directory. An explicitly supplied `--repo-root .` asserts the current directory. With neither selector the current directory still selects the default database. Keep origin and a live source location distinct. Where verified mode is chosen, preserve its ownership check, source captures, and active-generation check.

Stored mode can finish on its pinned generation if the path is replaced. Use a distinct versioned batch envelope for stored mode or normalized children. In stored mode, report `freshness: stored`, `freshnessStatus: unchecked`, the recorded origin and zero captures. Stored fingerprints describe the opened generation. Only verified mode may report a live source window or end-of-window generation observation. Children carry the parent's stored authority and generation. A mode-aware batch renderer and structured output retain the existing byte cap and external CLI failure rules. This deliberately reuses the snapshot reader rather than implementing batch as a loop of independent CLI invocations.

### 3. Aggregate complete named-library results

Use `search batch --indexes FILE --queries FILE`. The index file is a JSON array of entries of the form `{"name":"mathlib","repoRoot":"/path/to/mathlib","indexPath":"/path/to/mathlib.sqlite","freshness":"verify"}`. Resolve relative manifest paths from the manifest directory. Require a repository for verified entries and either a repository or explicit database for stored entries. The manifest is mutually exclusive with single-index selectors. An entry may inherit the top-level batch freshness default. Use one common query list with each scope resolved independently by its library. An empty scoped population carries that library's normal scope evidence.

Start with a sequential, ordered loop over bounded entries and reuse the single-library read path exactly once per entry. A manifest can specify at most eight names, and the combined number of library-query executions is capped at 128. Apply the selected `--max-output-mib` budget to each per-index batch and again to the complete serialized aggregate, including group headers and diagnostics. A per-index overflow yields a bounded unavailable group. Aggregate overflow fails before publication and preserves any existing output file. Validate manifest structure and the common query arguments once before opening any databases. Resolve repository-specific scopes and check index availability and ownership inside each group. As the read operations are independent, avoid combining databases or advertising a shared source-validation window. Report available, partial and unavailable results at the aggregate level with the existing operational nonzero exit convention for partial and unavailable responses. Preserve per-entry failure and success in the structured result. Use a versioned aggregate schema with each group carrying a batch result or a scoped error. Grouping preserves same-named declarations and lets the caller inspect local import candidates alongside archive results.

## Field replay targets

Check returned declaration identities in the repository-scope normalized results. A direct lookup by qualified name can confirm fixture contents but cannot establish retrieval by fragments. Use a portable fixture with a separately extracted conclusion to test ranking, since the RH targets exercise signature-only discovery. Use an existing archive index as described in the [RH walkthrough](../../../docs/RH_INDEX_EXAMPLE.md). These are search acceptance targets. Each named declaration was located in the earlier source inspection.

| Target declaration | Normalized fragments |
|---|---|
| `GlobalTheory.GaussWidths.integral_gauss_mul_gauss` | `‖y-a‖^2` and `s * c / (s + c)` |
| `GlobalTheory.RestrMeas.lintegral_fintype_prod_eq_prod` | `AEMeasurable` and `∂(Measure.pi μ) = ∏ i` |
| `GlobalTheory.CompanionTheory.Ar.Short.Crofton.LayerCake.dy_eq_tsum` | `dy k x =`, `∑'` and `else 0` |

Keep the raw literal commands in the replay. On the observed RH snapshot, `(s * c / (s + c))` produced one result. `‖y - a‖ ^ 2` produced nine and `‖y-a‖^2` produced zero. For the product integral, also search Mathlib and Mf for the corresponding real or nonnegative product integral and inspect the distinct source and measure assumptions.

## Risks / Trade-offs

- **Large archive scan cost.** Use the existing RH index for a bounded read-only comparison in stored mode on the Gaussian, product-integral and tail-sum queries. Record per-mode elapsed time and peak memory on the same machine and compare against the existing literal batch and repeated stored single-query calls. Cap each field run at two minutes. If direct normalized ranking is too costly, keep the contract and optimize the query or add a recall-preserving prefilter before treating archive performance as qualified.
- **Ambiguous normalization or missing conclusions.** Use fixtures with identifiers, symbols, quoted contents, repeated fragments and source-only declarations. The reported match policy and field evidence stay lexical. Test that unchanged literal invocations preserve their existing ordering and coverage.
- **Per-library races and limits.** Reuse the source-race and generation-replacement checks for verified entries and test the pinned-read case separately for stored entries. Test mixed successful and failed groups as well as aggregate overflow using small independent indexes.

## Migration Plan

Land normalized fragments, then stored batching, then named-library aggregation. The first implementation targets the existing index schema. Update the CLI reference and installed skill examples with the versioned outputs and scope examples for each increment. Keep the previous command forms usable during rollout.
