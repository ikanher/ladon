# Historical ideas and measured schema migration

Ladon stores historical mathematical attribution separately from Lean implementation dates,
formal dependency edges and proof authority. One declaration may implement several ideas.
A historical prerequisite edge points from the earlier ingredient to the dependent idea;
year order alone never creates an edge. Incomplete or disputed chronology is permitted.
The historical graph must be acyclic, independently of the formal graph.

## Commands

Using the updated Ladon checkout (older installed versions do not have these commands):

```sh
ladon proof-search index migrate --repo-root /path/to/project --format json
ladon proof-search index ideas-sync --repo-root /path/to/project --format json
ladon proof-search index ideas --repo-root /path/to/project --limit 100 --format json
```

All accept the usual `--index-path`. Migration accepts an existing v6 index and
adds the v7 historical tables without running Lean, scanning sources, re-extracting
signatures or clearing semantic evidence. Repeating it on v7 is a no-op. v5 snapshots
remain readable; they need a separate ordinary upgrade before this migration.
The v7 physical layout retains the v6 **proof-input** schema identity. Historical
metadata has its own input digest and cannot make a stale proof fresh.

Migration uses the existing publication lock, a unique sibling recovery snapshot,
a temporary working copy and durable atomic replacement. The response gives the
snapshot path. Failure before replacement leaves the original database unchanged;
a post-replacement directory-sync failure reports uncertain durability. Close other
SQLite writers first: an existing WAL sidecar is rejected. Do not write concurrently
through a connection that bypasses Ladon's publication lock. Recovery snapshots are
retained for operator review and must not be treated as current evidence automatically.

## Authored catalogue

Keep `ladon-ideas.json` at the Lean repository root under version control. It is
read on build, ordinary source refresh and explicit `ideas-sync`. Sync never clears
proof projections. A missing file retains existing indexed annotations and reports
`missing-retained`; to remove them intentionally, sync an explicit empty catalogue.
Rebuilding an existing annotated database is refused if its catalogue is missing.
Building to a different path cannot reconstruct annotations that existed only in
the old database; restore the authored catalogue first.

The top-level format is exact (unknown fields, duplicate keys and duplicate record
IDs fail). All five arrays are required; an empty catalogue is:

```json
{"schema":"ladon-ideas-v1","ideas":[],"sources":[],"attributions":[],"links":[],"dependencies":[]}
```

Each record has exactly these fields; nullable fields must still be present:

| Array | Fields |
|---|---|
| `ideas` | `id`, `title`, `statement`, `scope_note` |
| `sources` | `id`, `citation`, `version`, `url`, `artifact_path`, `artifact_sha256` |
| `attributions` | `id`, `idea_id`, `source_id`, `source_locator`, `year_start`, `year_end`, `precision`, `dating_basis`, `review_status`, `reviewer`, `reviewed_at`, `is_selected` |
| `links` | `id`, `idea_id`, `package`, `module`, `declaration_name`, `statement_sha256`, `relation`, `review_status`, `evidence_locator`, `note` |
| `dependencies` | `id`, `parent_idea_id`, `child_idea_id`, `evidence`, `review_status` |

IDs and ordinary fields are strings. Nullable source fields are `url`,
`artifact_path`, `artifact_sha256`; nullable attribution fields are `source_id`,
`source_locator`, the two years, `reviewer`, `reviewed_at`. Hashes are lowercase
SHA-256 hex. `is_selected` is integer 0 or 1, not JSON boolean. Years are integers
between 1 and 9999, never guessed from filenames or timestamps.

- `precision=year`: both endpoints equal; source and nonempty locator required.
- `precision=decade`: start divisible by ten, end=start+9. For example 1950–1959
  projects as `idea_year=null`, `guess_of_the_decade=1950`.
- `precision=range`: inclusive ordered endpoints; no invented representative year.
- `precision=unknown`: both endpoints null, with an explicit `dating_basis`.
- Status is `proposed`, `reviewed`, `disputed` or `rejected`. A reviewed attribution
  needs a reviewer and review date. Selection requires reviewed status; a partial
  unique SQL index permits at most one selected attribution per idea. Competing
  claims remain stored. Review is a recorded human assertion, not automatic validation.
- Link relation is `formalizes`, `generalizes`, `adapts` or `uses_ingredient`.
  Its statement hash is SHA-256 of the exact UTF-8 indexed `type_text`, with no
  normalization. Truncated or unavailable signatures never resolve. Use package,
  module and declaration `name` from the index, not a guessed qualified name.
- Dependencies require evidence. Self-edges are forbidden by SQL; synchronization
  checks the entire directed graph for cycles before accepting it. The catalogue
  API is the supported writer; arbitrary SQL edits bypass its full-DAG validation.

The complete SQL DDL is in `src/ladon/idea_history_schema.py`. Validation is limited
to structure, references and graph consistency; Ladon does not assert historical
priority or verify a citation's contents. Catalogues are limited to 8 MiB.

## Queries and correspondence

Name/type results and stored lineage nodes carry `historicalIdeas` arrays.
Unlinked declarations explicitly report null dates and `unassessed`. Stale links
remain visible with null projected dates. Historical review and link review are
separate fields. `ideas` returns competing attributions, durable links, binding
resolution, input status and bounded prerequisite edges, with per-table truncation.
It is not a transitive closure query. Coverage counts report resolved declaration
associations and selected ideas separately from theorem counts.

SQL views `idea_dates` and `declaration_idea_dates` expose `idea_year` and
`guess_of_the_decade`. SQL consumers must check binding `resolution` before using
a declaration's date. Durable links are independent of disposable declaration IDs;
refresh rebinds by package/module/name and statement hash. Changed statements are
`stale`, absent names `missing`, multiple matches `ambiguous`. No unresolved link
is silently reassigned to a different proposition.

## Migration damage metrics

The migration automatically compares the recovery snapshot and unpublished copy.
`ladon.migration_metrics.compare_databases` can also compare arbitrary file copies.
For every old table it streams canonical, type-preserving sorted row digests and
row counts over all old columns. Only the three exact physical-schema metadata
substitutions are allowed. It also checks SQLite integrity, foreign keys, historical
cycles and selected ordered SQL observations. Same-count swaps and authority
promotion are failures.

`dataLoss`, `linkLoss` and `queryLoss` are **fractions of failed invariants**, not
estimates of missing theorem percentages. Each exposes failed and checked counts.
Zero observations give a null fraction, not a perfect score. `accepted` requires
zero hard violations. Detailed table/query results remain in the report. Storage
ratio and elapsed time are reported separately; historical enrichment is separate
from preservation. These metrics do not measure the truth of new attributions.

Qualification uses adversarial fixtures, populated semantic/lineage fixtures and
independent copies of real indexes. Review storage ratio above 1.10 or warm query
median ratio above 1.25, reporting absolute times for sub-millisecond noise. Any
unresolved preservation failure blocks acceptance. Results are recorded in the
owning OpenSpec change, not inferred from a successful command exit alone.
