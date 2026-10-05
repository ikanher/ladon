# Authored proof reading guides

`ladon result guide` reads an ordered explanation alongside a result manifest's
stored evidence. The guide is a separate, attributed document. It does not run
Lean, contact a model, retrieve literature, refresh a store, or establish that a
lemma applies to a new goal.

```bash
ladon result guide result.json --guide-inputs guide.json --artifact source-map.json
ladon result guide result.json --guide-inputs guide.json --section citations
ladon result guide result.json --guide-inputs guide.json --section reviews
ladon result guide result.json --guide-inputs guide.json --section targets --claim claim-id
```

Repeat the explicit artifact and lineage inputs on each command that needs them.
Sections are `steps` (default), `citations`, `reviews`, `correspondence`, `targets`,
`checking`, `assumptions`, `lineage`, `evidence`, and `exposition`. `--claim` and `--target`
select exact IDs and combine conjunctively. Step, citation, and review selection
uses the step's own claim and target bindings. Structural sections also include
current guide supporting targets, even when no correspondence link names them.
This association does not add a claim-to-theorem correspondence judgment.

For a focused paragraph/coverage view, use `--section exposition --claim ID
--component ID`, with the existing `--assessments` companion if supplied. See
[selected components and paragraph review](RESULT_EXPOSITION.md) for current
and historical review boundaries, exact statement authority and missing premises.

The guide keeps authored order and each step's original one-based `position`.
Declaration dependencies and dossier derivations retain their existing owners'
coverage and limitations; they do not determine the reading order. Missing guide
inputs produce an explicit unavailable step while structural navigation remains
usable. `guideStatus: historical` means the manifest revision or at least one
step is historical. Each citation and review has its own currency, so an available
guide can still contain historical reviews.

## Companion format

The packaged [schema](../src/ladon/schemas/ladon-result-guide-v1.schema.json) is
`ladon-result-guide-v1`. Its root contains exactly `schema`, `resultId`,
`manifestRevision`, `steps`, `citations`, and `reviews`. Manifest v1 is unchanged.

| Population | Required content |
| --- | --- |
| `steps` | `id`, `revision`, `claimId`, `claimRevision`, `targetRevisions`, `purpose`, `explanation`, `sources`, `author`, `prerequisites` |
| `citations` | `id`, `revision`, `stepId`, `stepRevision`, `work`, `locator`, `relationship`, `assertion`, `submitter` |
| `reviews` | `id`, `scope`, `stepId`, `stepRevision`, `targetRevisions`, `reviewer`, `status`, `rationale`, `timestamp` |

Each target binding contains `targetId` and `revision`. Each source contains a
`locator` and content `digest`; every step needs at least one source. Each
prerequisite contains `stepId` and `revision` and must name an earlier step.
Prerequisites are authored dependencies between explanations, not inferred proof
edges. Empty target and prerequisite arrays are allowed.

Authors and reviewers have `identity` and `kind` (`human`, `model`, or `tool`).
These identities are self-attributed. Citation `submitter` is an identity string.
A citation's `work` has `id`, `title`, `authors`, and optional `url` and
`persistentId`. A locator identifies the relevant section, theorem, or passage.
The relationship is `background`, `uses-result`, `related-method`, or
`attribution-claim`. URLs are metadata; Ladon does not fetch or verify them.
Conflicting origin assertions stay separate. A citation is not evidence of
priority or novelty, even if a review approves it.

Review `scope` is `explanation` or `attribution`; `status` is `approved`,
`with-differences`, or `disputed`. An attribution review must additionally carry
`citationId` and `citationRevision`; an explanation review must omit them.
Timestamps include a timezone. A review referring to the present step revision
must carry exactly that step's target revision map. Older step revisions can
retain historical target bindings. Correspondence reviews remain in the
manifest, displayed under `--section correspondence`; they do not approve the
explanation or its citations. Stored checker evidence remains independent of
all these judgments.

IDs are limited to 256 UTF-8 bytes, actor and submitter identities to 1,024,
and text fields to 65,536. Arrays contain at most 10,000 entries; the total
across all arrays is at most 100,000. Companion files are at most 16 MiB.
Objects are closed, references must name existing rows, and duplicate IDs,
forward prerequisites, and revision digest mismatches are errors. The packaged
schema describes shape; runtime validation additionally enforces UTF-8 byte
limits, aggregate bounds, digests, and cross-row semantics.

## Revisions and historical reviews

Use the public Python API to compute revisions after authoring a row:

```python
from ladon.result_guide_inputs import guide_revision, validate_result_guide

step["revision"] = guide_revision("step", step)
citation["stepRevision"] = step["revision"]
citation["revision"] = guide_revision("citation", citation)
validated = validate_result_guide(guide, manifest)
```

The hash is SHA-256 of `ladon-result-guide-v1/KIND` followed by one NUL byte and
the row's canonical UTF-8 JSON, excluding only its own `revision` field. Canonical
JSON sorts keys, uses compact separators, and preserves Unicode. The value is
prefixed with `sha256:`. Step revisions therefore include purpose, prose,
sources, author, claim/target revisions, and prerequisite revisions. Citation
revisions include work metadata, cited passage, relationship, and assertion.

A step is current only when the manifest, claim, targets, and every earlier
prerequisite agree with its bindings. Historical prerequisites propagate to
dependent steps. A citation must bind the exact current step; an attribution
review must also bind the exact current citation. Editing an explanation or
cited passage preserves old reviews as historical. Updating a prerequisite
requires an explicit decision about each dependent explanation's binding.
Recomputing hashes does not reapprove any review.

`validate_result_guide` returns detached data. `guide_currencies` validates its
inputs and returns `steps`, `citations`, and `reviews` maps keyed by ID. Projection
validates the complete companion, canonical artifacts, check receipts, and
explicit lineage selections before returning selected rows.

## Inspecting and reusing a lemma

1. Read the step's purpose, explanation, source locator, and revision bindings.
2. Select its exact target with `--section targets --target ID` to inspect the
   supplied statement and source. The step shows them only when its referenced
   target revision matches; historical target text is unavailable unless supplied
   separately in its original artifact.
3. Inspect `checking`, `assumptions`, `lineage`, and `evidence` as needed, retaining
   their distinct guarantees. Structured hypotheses remain unavailable when the
   existing owner does not extract them. A rendered type is not a new hypothesis
   analysis. Missing evidence is not proof absence.
4. Use an explicit candidate application or other appropriate check for a new
   goal. Every guide page reports `reuseApplicability: not-checked`.

Pages accept `--limit 1..100` and fit 32 KiB in both JSON and text, including the
newline. Text contains the same named JSON values. Follow `pagination.nextCursor`
with unchanged inputs, selections, limit, and stored observations. Any changed
companion, canonical population, or selected stored lineage observation
invalidates continuation. Timing observations do not enter cursor identity.

`fieldOmissions` names each clipped field and an exact source reference. Guide
references use `input: guide-inputs`, the companion's canonical JSON SHA-256
digest, and a JSON pointer such as `/steps/0/explanation`. Target statements and
sources refer back to the manifest. Read those original supplied bytes for full
text. Pagination makes every selected row reachable; clipping is not evidence
loss or a change to the source document.

The [small example](../tests/fixtures/result_manifest/finite-map.guide.json)
accompanies [the illustrative manifest](../tests/fixtures/result_manifest/finite-map.json).
Copy both files anywhere and run:

```bash
ladon result guide finite-map.json --guide-inputs finite-map.guide.json
ladon result guide finite-map.json --guide-inputs finite-map.guide.json --section correspondence
```

Its digests and source are illustrative. It highlights an additional finiteness
hypothesis and makes no checked-formalization claim.
