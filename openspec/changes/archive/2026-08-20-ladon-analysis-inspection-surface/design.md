## Context

The large-inventory source index contains far more evidence than normal report
projections can carry. On the observed Matrix-Factorization snapshot, Ladon counted
roughly 138,000 lexical declaration candidates but retained only about 7,500 in
the report summary. The current installed surface can inspect findings and run a
small set of atlas queries, but it cannot navigate arbitrary declarations,
modules, import sites, audit commands, options, resources, or lexical proof
mechanisms.

This child adopts rather than replaces:

- `ladon-large-inventory-scale-contract` for source-index ownership, fingerprints,
  caches, and bounded payloads;
- `ladon-actionable-findings-workflow` for finding identities and next actions;
- `ladon-lean-audit-command-surface` for audit/result authority;
- `ladon-installed-reportset-workflow` for atlas and canned-query algorithms;
- `ladon-cli-execution-contract` for streams, exits, and formats;
- `ladon-report-contract-v2` for schema compatibility; and
- `ladon-elaborated-declaration-surface` and `ladon-proof-xray-roadmap` for Lean
  declaration and future elaborated proof-shape authority.

The child starts after the umbrella's report `coverage-foundation`,
declaration/audit integrity, and generated-family candidate work establishes the
shared page counts and canonical row kinds. This avoids shipping a temporary
inspection schema that cannot expose later candidate dimensions.

## Goals / Non-Goals

**Goals:**

- Provide one ordinary installed inspection grammar for canonical analysis
  evidence.
- Keep list operations bounded, deterministic, paginated, authority-bearing, and
  coverage-bearing.
- Make late declaration rows and exact source anchors reachable without inflating
  every report.
- Reject stale or incompatible indexes and cursors.
- Add useful lexical proof-mechanism, scope-context, generic option, and resource
  navigation.
- Preserve text/JSON semantic parity and existing process/output discipline.

**Non-Goals:**

- No LLM-specific command, endpoint, default, ranking, or evidence.
- No implicit source analysis, Lake build, Lean helper, or VCS command when
  inspecting an existing artifact.
- No new atlas engine, report schema family, cache, or source inventory.
- No lexical claim about elaborated tactic identity, dependencies, rewriting,
  instance selection, proof success, or theorem quality.
- No unbounded default dump of the source index.

## Decisions

### 1. Use one registry-backed inspection family

The installed CLI will expose one inspection family whose nouns select registered
canonical collections: modules, declarations, imports, audits, options, resources,
and proof mechanisms. Nouns share filter, pagination, exact-lookup, rendering,
diagnostic, and output-channel machinery.

The implementation must resolve the final caller-neutral spelling against existing
CLI conventions before dispatcher work begins. It must not add a second command
whose only distinction is the expected caller.

Alternative considered: add independent top-level commands for each table. That
would multiply argument, pagination, error, and rendering contracts.

### 2. Query canonical rows through typed adapters

Each noun adapter maps a canonical report or source-index table into a common query
row containing stable identity, schema/source fingerprint, population, scope,
authority, source anchor, and collection-coverage reference. The adapter returns
references to canonical rows; it does not create a second authority-bearing
inventory.

Existing atlas queries remain owned by the report-set workflow. Inspection may
link to or invoke those operations but does not reimplement graph algorithms.

Alternative considered: parse rendered JSON generically. Generic dictionary
walking cannot enforce authority, stable identity, or table-specific filter
vocabularies.

### 3. Bind deterministic pagination to evidence and query identity

Every list request normalizes its noun, filters, ordering, and page size into a
query fingerprint. A cursor binds that query fingerprint to the immutable
report/index artifact fingerprint and last stable ordering key. Pages expose
visible, matching total, omitted, and completeness.

The first implementation may use an opaque cursor or explicit offset/limit, but it
must guarantee disjoint stable pages over unchanged evidence and fail closed after
selected-evidence drift. Artifact-only mode validates the artifact and does not
read a live checkout. An explicitly live-repository-bound mode additionally binds
registered source/configuration fingerprints and rejects changes between pages.
An empty complete result, an incomplete result, and a stale query are distinct
states.

Alternative considered: paginate by transient array index without binding the
selected evidence. Artifact replacement or live-bound source changes can then
silently skip or repeat rows.

### 4. Keep inspection non-executing by default

Inspecting a supplied compatible report or source index reads only that artifact
and registered cache metadata. It starts no analysis phase or target-controlled
process. If a caller explicitly requests a combined analysis-and-inspect workflow,
that remains an ordinary composition through the existing analysis contract and
is visibly recorded.

Alternative considered: transparently regenerate missing evidence. That makes
lookup latency and side effects unpredictable and prevents stale-index diagnostics.

### 5. Extend the source index with lexical navigation rows

The existing comment/string-safe scanner will emit bounded rows for:

- supported tactic-command tokens and attributes inside safely recognized
  declaration ranges;
- namespace, section, variable, `omit`, local notation/instance, `open scoped`,
  and export context;
- every safely parsed `set_option`, with bounded raw value and option class; and
- normalized finite/unlimited value and lexical scope for supported resource
  options.

Rows retain parser status and lexical authority. Unsupported syntax yields
unresolved evidence rather than guessed binding or semantic state. Aggregate rows
link to bounded canonical members and do not fabricate one source location.
Normalized unlimited resource settings and explicit fingerprinted policy matches
are the only pressure classes in this child. Numerically large finite values
without policy remain navigation evidence; distribution-derived thresholds are
deferred. Eligible pressure rows expose canonical region-registration data and
ordinary inspection actions, but this child does not synthesize complete
review-region objects; the report child's
`snapshot-and-region-integration` milestone owns that integration.

Alternative considered: wait for proof-xray and Lean enrichment. That would leave
the default large-repository text workflow unable to navigate dominant proof
mechanisms.

### 6. Separate lexical rows from optional Lean enrichment

When a report contains Lean-resolved declarations, audit results, or future
proof-xray evidence, inspection links the lexical and Lean rows with their distinct
authority, toolchain, scope, and completeness. Absence or failure of Lean evidence
does not remove lexical navigation and never causes lexical fields to be presented
as Lean results.

Alternative considered: merge both into a best-effort row. Consumers could no
longer tell whether identity or proof shape was parsed or elaborated.

### 7. Render one selected page through the shared CLI contract

Text and JSON render the same normalized page model. JSON stdout contains one
document; diagnostics remain on stderr. Text is bounded and reports query,
coverage, authority, source anchors, and a next-page/exact-lookup route. Invalid
filters use invocation-error behavior; stale or incompatible evidence uses a
structured data-compatibility diagnostic.

Alternative considered: render directly from each source table. Per-noun
renderers would drift in counts, nonclaims, and pagination behavior.

### 8. Gate scale and installed behavior

Portable fixtures include more rows than one page, late matches, comments/strings,
ambiguous scope syntax, generic and resource options, absent Lean enrichment,
stale cursors, and mismatched indexes. Installed-candidate gates verify help,
text/JSON parity, deterministic pages, clean channels, and zero Lake/Lean/VCS
execution.

The existing large-inventory performance and report-size gates remain required.
An optional live Matrix-Factorization observation records moving fingerprints and
counts without changing product thresholds.

## Risks / Trade-offs

- **[New lexical row kinds increase index size]** → use compact interned fields,
  measure the existing large fixture, and keep report projection separate from
  paginated index access.
- **[Cursor formats become compatibility surface]** → version cursors, bind schema
  and query fingerprints, and treat them as opaque.
- **[Generic filters can become an unsafe mini-language]** → use a finite typed
  vocabulary per noun and reject unsupported combinations before reading rows.
- **[Tactic and option counts invite semantic overreading]** → carry lexical
  authority and nonclaims on rows, aggregates, renderers, and documentation.
- **[Exact lookup from a report may lack full source-index data]** → report
  unavailable or omitted evidence with a compatible index route; never fabricate
  the row.

## Migration Plan

1. Register the page/query/coverage model and noun adapters without changing
   existing analysis defaults.
2. Version the source-index extensions and invalidate incompatible cached entries.
3. Implement module, declaration, import, audit, option, and resource inspection,
   then add lexical mechanism and scope-context rows.
4. Add exact lookup, stable pagination, text/JSON rendering, and documentation.
5. Run focused, installed-candidate, large-fixture, and optional live acceptance.

Rollback can remove the new command routing while leaving additive source-index
fields unread. Cached rows use a versioned fingerprint, so older binaries will not
silently accept an incompatible index.

## Resolved Interface Decisions

- The grammar is
  `ladon inspect <modules|declarations|imports|audits|options|resources|proof-mechanisms>`
  with exactly one of `--report PATH` or `--source-index PATH`, repeatable
  `--filter FIELD=VALUE`, optional `--id`, `--cursor`, and `--limit`, plus the
  established `--format` and `--output`.
- Artifact-only inspection is the default and reads no checkout. Explicit
  `--repo-root PATH` binds source-index inspection to live repository state and
  therefore participates in stale-source validation.
- Pagination uses an opaque, versioned cursor bound to the immutable artifact
  fingerprint, normalized query, page size, and last stable ordering key. Cursors
  are not user-editable filter syntax.
