# Portable result bundles (experimental core)

`ladon result export` packages one exact result revision and explicitly selected
local files. `ladon result verify` checks package integrity. Ordinary
`result inspect` and `result guide` read the bundle without its original checkout
or cache. These operations do not run Lean, a model, a network request or a
publication service. Integrity does not authenticate the producer or establish
mathematical correctness, correspondence, peer review or human understanding.

## Example

From the Ladon checkout, prepare the illustrative finite-map package:

```bash
ladon result export tests/fixtures/result_manifest/finite-map.json \
  --selection tests/fixtures/result_manifest/finite-map.bundle-selection.json \
  --output /tmp/finite-map.zip
ladon result verify /tmp/finite-map.zip
ladon result guide /tmp/finite-map.zip --section steps
ladon result inspect /tmp/finite-map.zip --section components
ladon result verify /tmp/finite-map.zip --extract-to /tmp/finite-map-unpacked
ladon result guide /tmp/finite-map-unpacked --section citations --format text
```

The illustrative theorem has an additional finite-domain hypothesis and no
canonical checking evidence. Packaging does not change those facts. Extraction
requires a new destination directory; failures preserve any existing output.

When someone supplies a complete bundle, pass its ZIP or extracted **directory**
to `result inspect` and `result guide`. Passing only the extracted
`manifest.json` selects the explicit-file workflow: companions are included
only when supplied through its corresponding options. Unresolved targets in
that invocation describe the supplied subset, not every artifact in the bundle.
Likewise, a guide's reference to an assessment does not automatically include
that assessment. Check the selected roles and explicitly include the companion
before handing the package to a reader.

## Select exactly what to disclose

The selection document is `ladon-result-bundle-selection-v1`. Required fields:

| Field | Meaning |
| --- | --- |
| `supplier` | Self-attributed `{identity, kind}`; kind is human, model or tool |
| `entries` | Explicit file choices described below |
| `lineageBindings` | `{entryId, databaseId}` selections for stored lineage |
| `identifiers` | Optional supplied `{scheme, value}` scholarly identifiers |
| `externalDependencies` | `{id, kind, reason}` and optional inert `locator` |

An entry has a unique `id`, a `role`, `disclosure` and `permission`.
`disclosure` is supplied, redacted, unavailable or not-collected. Only supplied
entries with `permission: include` are opened; they require a local `path`.
All others need an omission `reason`. Relative source paths resolve beside the
selection document. Absolute local source paths are permitted; source symlinks,
including intermediate components, are rejected.

Roles are artifact, guide, assessments, lineage, lineage-database, predecessor,
attachment, review and capsule. Guide, assessments and lineage are singletons.
Canonical artifacts, guides and assessments use their existing validators and
bounds. The `manifest` ID is reserved for the positional manifest input.

Review attachments additionally require `review` metadata with `author`
(identity/kind), exact `subjectRevision`, and `scope`. They remain opaque
attributed attachments; their inclusion does not apply their conclusions to the
current result. Identifiers and external dependencies retain the selection's
supplier. Local hashes are content identities, never newly minted scholarly IDs.

Excluded files are never opened or hashed. Their source paths and content hashes
are absent from the index. Included files are disclosed **in full**, byte for
byte: embedded paths or private text inside a selected file are not redacted
implicitly. Review the files you choose to include.

## Stored lineage

Select the lineage companion and every database to include explicitly:

```json
{
  "schema": "ladon-result-bundle-selection-v1",
  "supplier": {"identity": "example-producer", "kind": "human"},
  "entries": [
    {"id": "lineage", "role": "lineage", "path": "lineage.json", "disclosure": "supplied", "permission": "include"},
    {"id": "store", "role": "lineage-database", "path": "selected.sqlite", "disclosure": "supplied", "permission": "include"}
  ],
  "lineageBindings": [{"entryId": "exact-entry-id-in-lineage-json", "databaseId": "store"}],
  "identifiers": [],
  "externalDependencies": []
}
```

The binding's source path must match the database named by that lineage entry.
A database selection includes the whole file; use a dedicated evidence store
when a cache contains unrelated rows. Nonempty WAL/journal sidecars are rejected
because copying only the main file would not capture a consistent store.
Export does not rewrite or checkpoint the source database.

The original companion is preserved. The reader maps its database paths only
through verified bundle bindings; it never reads the original paths. Unbound
entries remain explicitly unavailable. Logical `bundle:sha256:…/…` references
keep pagination stable when the package moves. Changing any inventoried payload
changes the bundle identity and invalidates earlier continuation tokens.

## Format, limits and history

`bundle.json` uses `ladon-result-bundle-v1` with profile `core-v1`. It inventories
every payload's relative path, raw byte count and SHA-256, excluding only the
index itself. The terminal report includes the index digest. Canonical ProofIR
identities and manifest revisions remain independently validated and unchanged.

Export produces deterministic ZIP_STORED bytes with sorted members and fixed
metadata. Readers accept regular stored/deflated ZIP entries or an extracted
directory. They reject unsafe paths, case/Unicode aliases, symlinks, unsupported
or encrypted entries, undeclared payloads, invalid references and forged sizes.
The core profile uses classic single-volume ZIP; ZIP64, split-volume and
self-extracting layouts are unsupported.
Actual expansion is counted independently of declared ZIP sizes. Complete
validation precedes views or publication of extracted contents.

The archive and expanded-byte limits default to **256 MiB**, and the member
limit to **10,000**, including the index. `--max-bytes N` and `--max-members N`
set finite positive ceilings for export, verify and bundled inspect/guide.
Existing 16 MiB metadata, canonical evidence and collection limits still apply.
JSON/text summaries remain bounded by 32 KiB; full details are in the index.
These transport limits are independent of the 32 GiB Lean process memory cap.

Predecessor-role manifests must belong to the exact `previousRevision` chain.
Missing predecessor revisions remain explicit. After extraction, historical
manifests are inspectable at their inventoried paths and retain historical
reviews. No file named by an external locator is fetched automatically.

Replay is always reported as not-run, with unknown dependency coverage and
supplied external dependencies preserved. Optional capsule files are opaque
attachments in this core profile. Research-process integration and pinned
community-profile checks belong to the later full milestone.

## Request preparation and cost

Each bundle inspection or guide request validates the full selected inventory
and prepares one dossier in its private verified snapshot. Target-specific
checking cards reuse that request's validated receipt population. Evidence
outside the selected page still participates in validation. The snapshot is
released with the request; there is no persistent inspection session or cache.

The [r65 maintenance observation](../openspec/changes/ladon-result-understanding-and-release-umbrella/baselines/request-preparation-r65/REPORT.md)
retains matching output bytes and single-run request timings. Those timings do
not establish a general speedup or mathematical usefulness.
