## Context

See proposal.md for motivation. The completed r46 dossier already resolves exact canonical subjects, reads explicit lineage stores, retains independent checking dimensions and bounds both output formats. Its full receipt satisfies this child's starting dependency. `result guide` is currently rejected as unsupported.

## Goals / Non-Goals

**Goals:** compose authored explanation and citation records over the existing evidence owners. Keep annotation currency independent from resolution, correspondence and checker outcomes.

**Non-Goals:** narrative generation, citation retrieval, a new graph extractor, a theorem-hypothesis parser, or claiming applicability to a new goal. Missing structured hypotheses and missing exact derivation bindings remain unavailable.

## Decisions

### Versioned companion and attributable subjects

Use `ladon-result-guide-v1` with `resultId`, `manifestRevision`, ordered `steps`, `citations` and `reviews`. Every step names a claim revision, zero or more exact target revisions, a purpose, explanation, source locators with content digests, author identity/kind and earlier prerequisite step revisions. Steps and citations have domain-separated content revisions. Keep manifest v1 and its revision function unchanged.

Require existing claim/target IDs and unique collection IDs. Prerequisites must precede their dependent step, making evaluation iterative and stack safe. Changed manifest/claim/target/prerequisite revisions make a step historical; historical prerequisites propagate through dependent steps. Target metadata from a different revision cannot fill a historical reference silently. A claim-only explanation is valid and does not invent a formal mapping.

Citations are separate assertions bound to a step revision. Each retains a work ID/title, supplied authors, optional URL/persistent ID, exact passage/result locator, relationship, assertion text and submitter. The four relationship kinds follow the parent spec. No URL is read. Competing assertions are preserved as individual records without a priority verdict.

Alternative: extend manifest v1 or put annotations into native ProofIR. Rejected because the strict manifest and canonical checking owners serve different contracts.

### Review currency

Companion reviews concern explanation or attribution; correspondence remains in the manifest owner. Reviews name the exact step and target revisions, reviewer identity/kind, status, rationale and timestamp. Attribution reviews additionally bind an exact citation revision. Invalid scope/reference combinations fail validation. Historical review bindings remain readable. Current human reviews are attributed attestations, never authentication or a guarantee of understanding. Approval and dispute records remain separate.

Changing an explanation invalidates its reviews and attached citations until explicitly rebound; changing a citation invalidates its attribution review. Earlier prerequisite revisions are part of the step dependency binding. This conservative policy prevents annotations from inheriting approval after their explanatory context changes.

### Shared offline evidence and presentation

Add `result guide MANIFEST --guide-inputs PATH` with optional artifacts and lineage inputs, exact claim/target selectors, section, limit, cursor and format. Missing guide input yields explicit unavailable explanation data while structural navigation remains available. Sections include steps, citations, reviews, correspondence, targets, checking, assumptions, lineage and exact-subject evidence.

Factor the dossier's input preparation into a shared owner without changing existing inspect output. Reuse its target resolution, complete receipt validation, lineage acquisition, assumption origins and temporary exact-subject dossier. The latter retains existing bounded derivation and navigation observations; missing exact graph bindings remain unavailable. Authored reading order is never sorted by the dependency graph. Structural selectors include explicit supporting targets in selected current guide steps, without creating correspondence links.

Reuse the bounded page owner for both formats. Cursor binding includes the full companion, manifest, canonical artifact population, selected store observations and query. Exact references point back to guide/manifest rows, supplied artifacts or selected store rows. Arrays of steps, citations and reviews remain independently paginatable; clipped fields retain exact drilldowns. Validate all inputs before any selected view.

### Qualification

Installed fixture and real-exposition runs retain authored/model status and unknown review/assumption coverage. Start the field guide with the conditional theorem, counterexample and release-scope differences before supporting lemmas. Do not modify the frozen exposition or its original baseline. The full guide exit needs a compatible same-candidate dossier/prerequisite receipt, quality, supported installed runtimes and independent audit; the earlier r46 receipt cannot simply be relabeled.

## Risks / Trade-offs

- Broad or repetitive annotation joins could grow output → retain 16 MiB input, 10,000 rows per collection, 100,000 aggregate entries, 64 KiB text and existing 32 KiB/100-row pages; materialize only requested cards when needed.
- A review could outlive a prerequisite or cited passage → explicit revision bindings and historical propagation, with separate review collections.
- Exact declaration evidence may have no matching derivation graph → keep the owner's unavailable/coverage result and structural-only limitations; no name-based fallback.
- A shared preparation refactor could alter inspect → preserve existing installed contracts and compare fixture output directly.

## Migration Plan

The companion, public guide function and CLI command are additive. Rollback removes this layer without changing manifests, stored canonical artifacts or lineage databases. Preserve historical receipts and original field captures. Core portable bundles remain the next child after guide qualification.
