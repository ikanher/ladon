# Experimental result manifests

Use `ladon result validate` to check one supplied result manifest before building
claim-to-theorem dossiers. Validation checks the JSON shape, declared content
revisions, internal references, and whether supplied reviews still refer to the
current declared subjects. It does not load Lean, inspect canonical ProofIR,
authenticate reviewers, or establish informal/formal correspondence.

```bash
ladon result validate /path/to/result.json
ladon result validate /path/to/result.json --format text
```

JSON is the default. Success writes one bounded result to stdout and returns 0.
Invalid input or arguments return 2 with a structured stderr diagnostic; an
unreadable file returns 1. Neither failure emits a success result. There is no
implicit build, network request, index mutation, or reference download.

The portable illustrative example is
[`tests/fixtures/result_manifest/finite-map.json`](../tests/fixtures/result_manifest/finite-map.json):

```bash
uv run --locked ladon result validate tests/fixtures/result_manifest/finite-map.json
```

Its informal claim omits a finiteness assumption present in the supplied formal
type. A model-attributed review records that difference. Source/environment
digests in this example are illustrative, and no Lean check is claimed. The
output records one unmapped component, a current attributed review with
differences, and unresolved canonical evidence.

## Data and identities

The packaged schema is
[`ladon-result-manifest-v1.schema.json`](../src/ladon/schemas/ladon-result-manifest-v1.schema.json).
Top-level fields are `schema`, `resultId`, `revision`, optional `previousRevision`,
`title`, `claimInventory`, `claims`, `targets`, `links`, and `reviews`. Unknown
fields are rejected; this initial schema does not yet accept guides, research
logs, or bundle metadata.

- Claims have exact supplied statements, document locators/digests, and nonempty
  component-ID inventories. Components are local to a claim.
- Targets have a declaration name, supplied `typeText`, a portable source path
  and digest/project revision, and a toolchain/environment digest. Optional
  `subjectRef` names an artifact digest and subject ID. `validate` does not dereference it;
  `resolve` inspects only explicitly supplied local envelopes.
- Links name a claim, its mapped components, and one or more target IDs. Several
  claims can share targets; several targets can implement parts of a claim.
- Reviews name a link digest, claim revision, exact target revision set,
  attributed reviewer identity/kind, method, timestamp, rationale, status, and
  anchored differences. A differences status requires at least one difference.

IDs are unique within each collection. Subject revisions include their logical
ID and all supplied fields other than that object's own `revision`. The manifest
revision includes every nested field, including nested subject revisions. Links
have a digest used by reviews rather than a separate stored revision field.

Canonical bytes use JSON with sorted keys, compact separators, `ensure_ascii=False`,
`allow_nan=False`, and UTF-8 encoding, without Unicode normalization. Prefix the
bytes with `ladon-result-manifest-v1/KIND` and a NUL byte, then compute SHA-256 and
render it as `sha256:` followed by lowercase hex. `KIND` is `manifest`, `claim`,
`target`, or `link`. Hashes identify supplied content, not truth or authenticity.

Producers can use the Python helper to compute revisions:

```python
from ladon.result_manifest_io import content_revision

for claim in manifest["claims"]:
    claim["revision"] = content_revision("claim", claim)
for target in manifest["targets"]:
    target["revision"] = content_revision("target", target)
manifest["revision"] = content_revision("manifest", manifest)
```

Construct a new review with the intended claim/target revisions and
`content_revision("link", link)` before recomputing the manifest revision.
After editing a subject, retain older review bindings to preserve history.
Updating a review to new subjects is an explicit new review decision; the
validator never does that automatically.

## Reading the result

`status: valid` has the scope `offline-manifest-integrity`. With `validate`, canonical resolution reports `not-assessed` and
`canonical-evidence-not-loaded`, including when supplied artifact references look complete.

`mapping` counts producer-declared components and mappings. A complete declared
inventory is not independently observed formalization coverage. A zero unmapped
count does not establish that a compound mathematical claim has been proved.

`reviewSummary` distinguishes current from historical bindings. Conflicting
current statuses yield `disputed`; historical reviews cannot provide current
approval. Reviewer kind stays visible, so a model review is not a human
attestation. Current binding does not validate the rationale or reviewer identity.

At most 100 review observations are returned, with exact omission counts.
Complete input remains in the manifest; full dossier/drill-down commands are
not implemented yet. Text renders the same bounded sections as JSON.

## Resource limits and remaining work

Input must be a regular file of at most 16 MiB. Duplicate JSON keys, non-finite
values, invalid Unicode, excessive nesting, dangling required references, and
revision mismatches fail explicitly. V1 caps claims at 1,000; other collections
at 10,000 entries; aggregate collection entries at 100,000; explanatory strings
at 64 KiB of UTF-8; and compact output at 32 KiB. Individual identity/locator
fields have smaller schema limits.

The runtime implements the finite vocabulary of this packaged schema without
adding a JSON Schema dependency. Semantic checks add content hashes, internal
reference rules, portable paths, timestamp validity, UTF-8 byte limits, and the
aggregate cap beyond generic schema validation.

Canonical evidence resolution and the full claim-correspondence child exit
remain dependent on the authority-safe/discovery integration receipts. This
offline command has experimental readiness. It does not promote any existing
capability or satisfy those gates.

## Explicit canonical target resolution

```bash
ladon result resolve result.json --artifact environment.json --artifact source-map.json
ladon result resolve result.json --artifact environment.json --artifact source-map.json --target target-id
```

`resolve` validates the complete supplied ProofIR v3 envelope population before
selection, using the existing canonical owner. It reports resolved, ambiguous,
unresolved or stale targets separately from correspondence review. A nonexistent
name remains unresolved even when manifest integrity validation succeeds. No
reference is downloaded or searched by a similar name, and no registry is opened.

The initial exact profile requires an explicit artifact-qualified declaration,
a rendered type bound to its structural declaration identity, the same canonical
environment digest, and a source-map anchor with matching path/content digest
and an environment/fingerprint association. The source-map subject must name the
selected owner explicitly or be local to that same envelope. Weak/name-only
anchors stay unresolved. Duplicate anchors or environment owners stay ambiguous.
Supported toolchain descriptors are the canonical `name:version`, or the standard
`leanprover/lean4:vVERSION` spelling when the canonical prover is Lean. The exact
environment digest remains necessary; the version spelling cannot substitute for it.

`stale` here means a supplied manifest binding disagrees with the stored evidence.
It is not a live working-tree freshness measurement. `projectRevision` remains
producer-declared because source-map envelopes do not independently observe Git
history. Resolution neither replays a check nor establishes informal/formal
correspondence. It reports checking and current-source freshness as not-assessed.

JSON and text preserve the same bounded observations. At most 100 target and
link observations are selected within 32 KiB; exact complete-population status
counts and omission counts remain visible. Use `--target ID` to inspect an omitted
target from the same manifest revision and supplied evidence population. Each
explicit envelope must be a regular file within the existing ProofIR 8 MiB
artifact / 32 MiB aggregate input bounds. These canonical-input and compact-card
bounds are separate from the uncapped architecture-report sizing diagnostic.
Malformed supplied evidence fails before success output. Missing optional evidence
remains unresolved without implicit fetching or execution.

## Capturing a source association

A stored candidate check does not contain source anchors. To create an anchor
for an exact stored declaration, explicitly compile its owner source with the
same pinned Lean executable:

```bash
ladon proof-search check source \
  --repo-root /path/to/project --module Project.Module \
  --source Project/Module.lean --candidate Project.theoremName \
  --artifact environment.json --artifact check-run.json \
  --subject-artifact sha256:CHECK_ARTIFACT_DIGEST \
  --setup .lake/build/ir/Project/Module.setup.json \
  --lake-path /path/to/pinned/bin/lake --lean-path /path/to/pinned/bin/lean \
  --max-rss-mib 32768 --format json --output source-capture.json
```

`--setup` is optional. The supported profile uses whole-module Lean output,
empty plugins/dynamic libraries, and bounded setup options. Ladon discards
setup import paths and uses the selected compiled-library roots. It feeds an
exact source snapshot through stdin with the original logical filename and
writes fresh outputs into a temporary directory. It does not run Lake or
update the project's build outputs.

Success requires the fresh `.olean` to match the stored whole-module digest,
unchanged observed inputs, and a valid declaration range from that same run's
`.ilean`. The `ladon-source-association-v1` result embeds one canonical
`proofir.source-map` in `artifacts`. Save that envelope as `source-map.json`,
then supply it with the original environment and owner artifacts to
`ladon result resolve`. The source map refers to the existing owner; it does
not replace it. Failed or bounded runs emit no source-map artifact.

This observes source-to-compiled association. Checker acceptance, complete
transitive source freshness, and informal/formal correspondence retain their
separate status. Auxiliary import files are observed before and after the
run; historical environments currently bind primary `.olean` files only.
The operation does not authenticate supplied artifacts or isolate a hostile
filesystem. Resources report the configured limits, compiler elapsed time,
and sampled process-tree peak RSS. The 32 GiB cap is an execution allowance,
not a performance target.

Primary compiled inputs share a 16 GiB aggregate allowance with candidate
checking; each file remains limited to 512 MiB. Auxiliary observations retain
their separate 8 GiB allowance. These files are hashed as streams. The result's
`compiled` inventory reports primary and auxiliary byte totals separately from
compiler RSS, so large import closures can be identified without treating disk
input size as memory consumption.

## Offline result inspection

`ladon result inspect` adds component cards and stored checker observations over
an explicit manifest and canonical artifact population:

```bash
ladon result inspect result.json --artifact environment.json --artifact check.json \
  --artifact source-map.json --assessments assessments.json
ladon result inspect result.json --section targets --target target-id
ladon result inspect result.json --section checking --claim claim-id --limit 5
```

Supply the same artifacts and assessment companion on each command that needs
those observations. No implicit store lookup, index refresh, Lean execution,
network request or model invocation occurs. A target can resolve while its
claim correspondence remains unreviewed. A conventional-only component or an
unchecked implication adapter is an attributed assessment, never a proof-absence
or proof-completeness verdict.

Sections are `components` (default), `claims`, `targets`, `assessments`, `reviews`,
`checking`, `assumptions`, `lineage` and `evidence`. Claims and targets use their exact IDs;
combined selectors are conjunctive. Checking preserves the original operation,
results, guarantee, producer, environment and supported stored receipt. A
candidate application remains `exact-candidate-elaboration`; it is not a full
theorem replay. Mismatched source/type/environment and same-name evidence from a
different artifact retain historical/mismatched or unassociated bindings. Every
supplied receipt is validated, even when a different section is displayed.

The `evidence` section reuses the ProofIR dossier query on the exact declaration
owner, kind and local ID. It builds a disposable in-memory projection from the
supplied artifacts and retains the owner's observations, checks, coverage,
limitations and omissions. Name-only coverage does not establish coverage of an
exact subject. An unresolved target cannot attach a same-name dossier.

The `assumptions` and `lineage` sections can read explicit stored captures with
`--lineage-inputs`; the companion format is below. Axiom dependencies, placeholder
observations and imported frontiers retain their source and authority. Unsafe
facts remain lineage facts, not declared mathematical assumptions. Logical axioms
are not automatically proof gaps; an imported theorem is not automatically
unproved. Structured theorem hypotheses, declared external mathematical assumptions
and obligations remain unavailable where the selected owners do not extract them.
Candidate application context and pretty-printed types are not parsed into an
authoritative theorem-hypothesis inventory. Transitive coverage remains unknown.

`--limit` accepts 1–100 rows. Both JSON and text output fit 32 KiB including their
framing. `pagination.nextCursor` continues the same section with the same
manifest, companions, selected stored observations, canonical artifact population,
selectors and limit. Pass it
as `--cursor`; changed inputs/query or malformed cursors fail instead of silently
restarting. `pagination.total` counts selected stored rows, not all mathematical
proof obligations. A missing population remains unknown.

`fieldOmissions` records clipped strings or nested rows. Each row includes exact
input references; a reference consists of an input kind, content revision and
JSON pointer. Inspect those supplied bytes to recover full text. Clipped receipt
or canonical fields are presentation excerpts; use the referenced original
artifact for integrity validation. Text renders the same JSON values per named
section, retaining all evidence dimensions and omissions.

Lineage references additionally identify the resolved database path, selected
closure, observation revision, table, ordering and row offset. Their JSON pointer
selects a field in that stored row. `lineage-selection-query` references identify
the companion entry by ID and content revision and the deterministic stored
selection query. `supplied-artifact-dossier` references identify the supplied
artifact population digest, exact subject and query limit; their pointer selects
the original dossier query output. Keep those inputs unchanged for drilldown.

## Explicit lineage selections v1

`--lineage-inputs PATH` accepts the packaged
`ladon-result-lineage-inputs-v1.schema.json` contract. Example:

```json
{
  "schema": "ladon-result-lineage-inputs-v1",
  "resultId": "my-result",
  "manifestRevision": "sha256:<manifest digest>",
  "entries": [{
    "id": "capture-1",
    "targetId": "target-id",
    "targetRevision": "sha256:<target digest>",
    "database": "capture.sqlite",
    "closureId": "<exact stored closure ID>",
    "identity": {
      "repository": "/path/to/project",
      "source_fingerprint": "<capture source fingerprint>",
      "configuration_fingerprint": "<capture configuration fingerprint>",
      "toolchain_identity": "<capture toolchain identity>",
      "base_generation_identity": "<capture base generation>",
      "helper_identity": "<capture helper identity>",
      "schema_generation": "<capture schema generation>"
    }
  }]
}
```

Replace the placeholders with the exact existing capture values. Relative database
paths are relative to the companion file. Databases are opened read-only, with
no discovery, refresh or Lean execution. The selected closure must be the exact
active capture for the supplied target name and identity. Missing databases,
missing closures, mismatched selections, stale source/configuration/toolchain
identities and malformed databases remain distinct. Changed manifest or target
revisions make a selection historical; malformed inputs fail even when their
section is not displayed.

The old lineage schema does not contain a canonical declaration/source-digest
link. Consequently the association is **producer-selected**, environment binding
is **not established**, and current-source freshness is **not assessed**. The
owner's `fresh` status means agreement with the supplied capture identity. It
does not prove agreement with the current checkout or informal claim.

The companion accepts at most 1,000 entries and 16 MiB. Each selected store read
retains up to 10,000 trust rows, frontier nodes and omission rows per collection;
truncation is explicit with exact drilldown references. Aggregate acquisition is
limited to 100,000 rows and 32 MiB across all selections, and individual stored
text fields to 64 KiB. These are read bounds, independent of the existing 32 GiB
Lean execution limit. Display pagination never turns bounded or missing trust
coverage into a complete assumption inventory.

## Component assessment companion v1

The packaged `ladon-result-assessments-v1.schema.json` describes the separate
optional `--assessments` input. Manifest v1 remains unchanged. The root fields
are `schema`, `resultId`, `manifestRevision`, and `assessments`. Each row requires:

- `id`, `claimId`, `componentId`, `claimRevision` and `targetRevisions` (each with
  `targetId` and `revision`).
- `kind`: `conventional-only`, `unassessed`, `source-correspondence`,
  `unresolved-target`, or `reported-implication-without-checked-adapter`.
- `author` with a supplied `id` and `kind` (`human`, `model` or `tool`), plus
  `basis`, `scope`, `differences` (text array) and `evidenceRefs` (text array).

The companion is capped at 16 MiB, 10,000 assessment rows and 100,000 aggregate
collection entries. Each explanatory item is limited to 64 KiB UTF-8. Unknown
fields/versions, duplicate row IDs and dangling references fail validation.
Multiple suppliers may assess the same component; all assessments are retained.
When manifest and claim revisions are current, the supplied target set must
match that component's mapping. A changed manifest, claim or target revision
makes the old assessment historical. Historical references must still name
subjects present in the supplied manifest. Neither supplier identity nor claimed
human review is authenticated by these fields.
