## Context

See proposal.md for motivation. The existing result resolver validates a whole canonical artifact batch and binds exact declaration, structural type, environment and source identities. The theorem evidence and lineage query owners operate on explicitly selected stored SQLite projections. The real exposition capture is immutable field evidence, not an independent human review.

## Goals / Non-Goals

**Goals:** preserve these existing owners while composing result-level inspection. Keep schema validation, source binding, stored checking and attributed assessments separate. Expose unavailable extraction and unknown transitive coverage explicitly.

**Non-Goals:** new Lean extraction, a new ProofIR family, automatic review or proof-coverage scores. Inspection must not run a checker, refresh an index or modify a store.

## Decisions

### Versioned companion

Keep manifest v1 unchanged. `ladon-result-assessments-v1` is a bounded optional companion with `resultId`, `manifestRevision` and `assessments`. Each assessment names its ID, claim/component and claim revision, target revision set, kind, author identity/kind, scope, basis, differences and supporting references. Different suppliers can assess the same component; assessments are not collapsed into one verdict. A changed manifest, claim, target or component mapping makes old assessments historical. Current mappings must match the assessment's target set; malformed internal references fail before display. Unsupported versions fail with an invocation diagnostic. Conventional-only, unassessed, unresolved-target and reported implication without a checked adapter are different assertions. None is a machine proof-absence conclusion.

### Shared bounded projection

`result inspect MANIFEST` accepts repeated `--artifact`, optional `--assessments`, `--claim`, `--target`, `--section`, `--limit` and `--cursor`. Sections expose components, claims, targets, assessments, reviews, checking, assumptions and lineage. Default component cards place the informal statement next to mapping, assessment differences, resolution and review gaps. Exact input references use manifest/companion revision or canonical artifact identity plus JSON pointer. Oversized fields retain byte/count omissions and these references, while all rows can be traversed by continuation. JSON/text share one evidence projection.

Cursors bind the exact manifest revision, companion content, canonical artifact population, section, selectors, limit and offset. Invalid or stale continuation fails; none silently restarts. Both formats including framing stay below 32 KiB, with at most 100 rows. Complete input validation precedes selection. Input caps reuse the result and ProofIR owners (16 MiB manifest/companion, 8 MiB per canonical artifact, 32 MiB canonical batch); assessment rows retain collection and aggregate entry ceilings.

### Existing evidence ownership

Expose an unbounded-by-display resolution core inside the existing resolver, then apply the established compact resolver projection unchanged. Inspection consumes this exact same resolution core, avoiding missed targets beyond its legacy 100-row display limit.

Stored canonical checks use `stored_check_receipt` with the exact input-owned environment artifacts. Candidate application fields are selected only from the canonical input-owned application; zero residuals describe that stored operation. Checks with no supported receipt retain their canonical operation, result, guarantee and coverage without inventing a receipt. Mismatched target/environment/source binding remains visible and cannot approve the selected target. Repository build observations may remain result-level evidence without applying to each target.

The existing theorem evidence and lineage readers remain separate optional explicit stored inputs. Exact subject/closure selection, stale/unavailable diagnostics and owner coverage must survive projection. Absence of one input does not trigger discovery. The assumption view distinguishes theorem statement hypotheses (structured extraction unavailable unless supplied by an existing owner), observed axioms, declared mathematical assumptions, placeholders, obligations and external frontiers. Candidate goal context is application context, not a complete theorem-hypothesis inventory; pretty-printed types are not parsed into an authoritative assumption list.

### Exact dossier and explicit lineage selection

The existing theorem query selects statements by name; result targets instead identify exact declarations. Add an exact subject entry point to that query owner and build its disposable in-memory projection from the already selected canonical artifacts. The `evidence` section retains the owner's separate sections and receipts. It cannot borrow another owner's same-name subject or name-only coverage. This uses the existing projection owner without discovering or refreshing a persistent index.

`--lineage-inputs PATH` selects a separate `ladon-result-lineage-inputs-v1` companion, bound to result/manifest and target revisions. Each entry identifies a database, exact active closure ID and all seven `LineageIdentity` fields. Relative database paths are relative to the companion. Inspection opens these databases read-only and checks the supplied identity through the existing lineage owner. The legacy lineage schema lacks canonical declaration and source-digest links, so the association remains producer-selected and environment binding remains not established. An owner's `fresh` status means agreement with the supplied capture identity, not verification of the current checkout. Historical selections and stale identities cannot support current evidence.

Stored trust rows and external frontier nodes retain their original kinds and scopes. Unsupported extraction categories remain unknown; neither logical axioms nor imported theorem boundaries become proof gaps. Acquisition is bounded to 10,000 rows per category and 100,000 aggregate rows; truncation retains exact database/closure/table references and unknown transitive totals. Continuation binds the selected store observations as well as the companion and existing inputs. Malformed selections fail before display, while missing inputs remain explicit unavailable observations.

## Risks / Trade-offs

- Stored canonical integrity is not producer authentication → retain producer identity and owner limitations.
- A compact field can hide a critical difference → flag truncation on the affected row with exact input pointer; paginate populations without silently dropping rows.
- Broad theorem-name queries can collect several owners → exact target subject selection gates attachment and query results retain their original identities.
- The exposition companion predates the generic schema → convert explicitly into a new derived file, retaining the original input and author/basis/differences unchanged; no silent in-place migration.

## Migration Plan

The new command and companion schema are additive. Existing manifests and resolve outputs retain their semantics. Rollback removes only the added reader/projection code and generated inspection reports; immutable input artifacts and the original field capture remain intact. Qualify the installed wheel outside the checkout, then record the child exit and prerequisite compatibility without promoting guide/bundle or human-review milestones.
