# Proof-search index v1

Ladon maintains a repository-local SQLite navigation index. Its
default path is `.ladon/index/proof-search.sqlite`; `--index PATH` selects an
external location. The public contract is the versioned CLI result, not these
private tables.

The v1 population is deliberately lexical. It stores Lake-discovered modules,
direct import occurrences, source-linked declarations, bounded lexical
signatures, structures, and an FTS5 declaration-search projection. Coverage
rows mark elaborated binders, declaration dependencies, and structure fields
unavailable. Consequently, search results are navigation candidates rather
than Lean-confirmed names, type matches, or proof facts.

## Constraints and access paths

Every build is written to a same-directory, PID-scoped temporary database and
published by atomic replacement only after `PRAGMA integrity_check` and
`PRAGMA foreign_key_check` pass. A sibling `proof-search.sqlite.lock` is a
persistent metadata carrier protected by a kernel-held advisory lock and an
unpredictable owner token; a second builder fails fast rather than racing to
publish. PID text alone never establishes ownership, and release closes the
descriptor without unlinking a path that a replacement owner could hold. The
canonical reusable database remains `.ladon/index/proof-search.sqlite`. The
default maximum database size is 1 GiB; `--max-index-mib` changes it. Lexical
signatures retain at most 16 KiB and record any truncation as omission evidence.
Query output is capped at 1,000 rows.

`index update` refreshes changed source modules and reuses unchanged lexical
extraction. When the supported index retains semantic, lineage or ProofIR
evidence, it first preserves a standalone SQLite snapshot, then publishes a
current lexical generation. Semantic overrides in otherwise unchanged modules
are re-extracted too. Update never invokes Lean or transfers old checks to new
source bytes. A no-op leaves the active database unchanged.

Snapshots live beside the index in `<index-filename>.history/`. Their names are
SHA-256 digests of the archived database, so different evidence under the same
source generation receives different identities. The active database contains
the history catalog. Move the database and its adjacent history directory
together, keeping the filename. Registered missing or corrupt snapshots block
updates; history inspection reports them as unavailable. Unregistered complete
files and interrupted backups remain protected and are listed separately.

The stored base-build size ceiling still governs the active candidate.
`index update --max-history-mib N` additionally bounds existing and proposed
history storage, including uncertain files. Without that option, history has
no configured ceiling. Nothing evicts evidence automatically. Each archival
update requires roughly one base-sized snapshot plus a temporary active copy;
status and update report active, registered-history and temporary bytes.

Publication uses the same writer lock as build and evidence acquisition.
Snapshots are synced before active replacement. A failure before replacement
leaves old active bytes intact; a failure after replacement reports
`publication-uncertain`. Inspect active status and history before retrying.
`source-changed` names a bounded sample of concurrent edits: retry after edits
settle. Unsupported layouts or changed toolchain/configuration require a build
to a **new** index path. Rebuild and prune cannot overwrite or delete a
history-owning index. History deletion is not supported.
Supported writers also reject a snapshot path as a publication destination,
including a symlink pointing to it. Hardlinked publication destinations are
unsupported, preventing in-place writers from modifying another linked file.

### Inspect retained evidence

Run from the project root (or supply its path):

```bash
ladon proof-search index update --repo-root "$PWD" --format json
ladon proof-search index history --repo-root "$PWD" --limit 10 --format json
ladon theorem lineage Project.theorem --repo-root "$PWD" \
  --history <snapshot-sha256> --refresh never --format json
```

History listing uses `ladon-proof-search-index-history-v1`, with bounded
`--limit`/`--offset` pagination. Historical lineage uses `ladon-theorem-lineage-history-result-v1`, preserves
the ordinary projection and adds `selectionBasis: historical-snapshot`, `freshness:
historical`, the original observation and `currentAssociation:
not-established`. Its receipt describes the original observation. An already
stale closure stays unavailable: selection does not repair its identity.
Historical selection requires `--refresh never`, runs no Lean, and works
without the original project. A joint relocation needs an explicit `--index`
pointing to the moved database. Fresh acquisition still requires the pinned
project and compiled imports, through ordinary current-mode lineage.

Private schema v6 recognizes the exact prior v5 layout for update and offline
reading. A changed v5 generation migrates to v6 after preservation; a no-op
keeps v5 unchanged. Older installed readers reject v6. Public current-mode
result schemas remain unchanged; unknown table or column extensions are
refused rather than discarded.

For a long rebuild, use `ladon proof-search index build --repo-root /path/to/project --progress`.
Bounded JSON events on stderr report discovery, module extraction, validation
and publication. Extraction events include processed and total module counts;
there are at most about twenty periodic updates plus the final count. The final
result remains on stdout. A publication event indicates an attempt, not success;
wait for the terminal result. Without `--progress`, these events are silent.

The schema currently requires 16 named B-tree indexes:

- declaration name, kind, module, namespace, package, source path, and
  structure membership;
- forward and reverse module-import edges;
- forward and reverse declaration-dependency edges;
- reverse aliases, package-owned modules, source-root libraries, field names,
  and omission reasons.

FTS5 provides the segmented name/signature search surface. Six foreign keys
constrain owned containment: imports to source modules, declarations to owner
modules, binders to declarations, structures to declarations and modules, and
fields to structures. Imported targets, dependency endpoints, and alias
endpoints intentionally remain raw names because external declarations may not
be present in a project-local v1 index.

## Matrix-Factorization observation

On 2026-08-08, generation
`37e6468117edd2a0b53930865320037b8835cc1abccb8ac5ba2fe6a853101ae0`
indexed the current Matrix-Factorization checkout:

- 3,742 modules, 8,416 direct imports, and 150,399 declarations;
- 2,048 lexical structure declarations;
- 302,407,680 bytes (289 MiB on disk);
- 52.34 seconds internal cold-build time and 123,184 KiB process peak RSS;
- all required indexes, FTS surface, foreign keys, integrity checks, and size
  constraints passed.

The checkout is live observational evidence, not a portable correctness
fixture. Its source fingerprint was
`5d75dbb93dd0d631a47e29f5a6887de6f211541714370d5c42f96a75bfe765b2`.

## Search comparison with `rg`

Seven warm repetitions compared the installed `ladon` entrypoint with staged
case-insensitive `rg -l` file filters. The `rg` pipeline required every query
token somewhere in the same file; the database required the tokens in one
indexed declaration name/signature. Times include process startup. DB-internal
times come from the result envelope.

| Intent | DB rows | DB internal | DB CLI median | `rg` files | `rg` median |
| --- | ---: | ---: | ---: | ---: | ---: |
| all-state corrector integrability | 1 | 1.17 ms | 139.74 ms | 36 | 37.09 ms |
| row/horizon integrability | 7 | 1.43 ms | 138.33 ms | 253 | 29.60 ms |
| normalized/physical scale | 2 | 0.97 ms | 139.91 ms | 66 | 22.27 ms |

The database was slower as a one-shot command because Ladon's general Python
CLI startup costs about 138 ms, while the indexed SQL work itself took roughly
1 ms. It returned source-linked declarations with kinds and signatures. The
file-level `rg` pipelines were faster but returned 36–253 files containing the
tokens anywhere, including unrelated declarations, proof bodies, and comments.

Using the DB declaration paths as a narrow—not mathematical—relevance oracle,
the `rg` file sets retained every matching declaration path but only 1.6–3.0%
of returned files contained one of those declaration-level matches. This does
not establish universal search precision: `rg` can find source text that v1
does not index, while v1 can miss elaboration-dependent relationships. It does
show the practical distinction between fast textual reconnaissance and a
slightly slower, structured CLI answer. Reducing general CLI startup is the
obvious latency follow-up.
