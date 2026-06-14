## Context

Ladon currently analyzes Lean projects through a clean-core pipeline: text or
Lean-parser extraction, pure module/declaration graph analysis, concise
findings, JSON/text rendering, atlas export/workflow summaries, and optional
ProofIR bridge evidence. The strongest product direction from external review is
to make this a Lean project observability and review-intelligence tool rather
than a prover, linter clone, documentation generator, or proof-agent frontend.

The current atlas workflow already answers some reviewer-routing questions over
report sets. The missing next layer is a first-class before/after review surface:
which Lean modules and declarations changed, whether theorem surfaces changed
semantically, whether imports became heavier, whether external evidence
attachments drifted, and which roots deserve reviewer attention first.

## Goals / Non-Goals

**Goals:**

- Define an umbrella path for `ladon diff` / Review Radar without committing to a
  UI or proof-engine rewrite.
- Make theorem-surface changes reviewable as structured facts, not raw textual
  diffs.
- Preserve source evidence, backend confidence, tool version, and non-claims on
  every review card.
- Let current text/parser-backed analysis produce useful results before any
  elaborated Lean backend is available.
- Provide a bounded extension point for future elaborated "Proof X-Ray"
  enrichment.

**Non-Goals:**

- Ladon does not validate theorem truth, proof correctness, witness adequacy, or
  ProofIR authority.
- Ladon does not own a full Lean kernel dependency graph unless a Lean-owned or
  explicitly elaborated artifact supplies that evidence.
- This umbrella does not require a graph database, web UI, editor extension, PR
  bot, Rust rewrite, automatic refactoring, or LLM prose generation.
- This umbrella does not replace Lake, doc-gen4, LeanDojo, Pantograph, Mathlib
  linters, or Quux/ProofIR claim-governance tools.

## Decisions

1. Review Radar is derived from reports and atlas workflow surfaces.

   The first implementation should reuse existing Ladon JSON reports, atlas
   diffs, reviewer cards, and optional bridge reports instead of adding a new
   storage backend. This keeps the product shape close to tested seams and lets
   `ladon diff --before ... --after ...` become a thin orchestration layer over
   stable report payloads.

   Alternative considered: build a UI-first dashboard or property graph first.
   That would make the data model harder to stabilize and distract from the
   near-term reviewer contract.

2. Semantic changelog starts with declaration surfaces, not proof terms.

   The first classifier should compare declaration identity, kind, source range,
   content hash, theorem type text when available, normalized binder/assumption
   summaries, conclusion summaries, imports, and doc/comment-only changes. It
   can classify proof-only changes when the declaration/theorem surface is
   stable but source hash or proof range changes.

   Alternative considered: wait for elaborated proof extraction. That would
   delay the most useful review signal even though current parser-backed
   declaration rows are already enough to flag many statement-surface changes.

3. Every field carries an authority label or inherits one from its source row.

   Text/parser observations are structural review context. Source hash/range
   joins establish attachment confidence only. ProofIR statuses remain quoted
   external context. Lean-elaborated facts, when added, must include backend,
   tool version, source hash, and extraction confidence.

   Alternative considered: collapse all evidence into one confidence score. That
   would hide the distinction between attachment confidence and proof authority.

4. Proof X-Ray remains optional enrichment.

   Elaborated theorem type, axiom/sorry/unsafe footprint, tactic skeleton,
   dependency names, and InfoTree/proof-shape rows should enrich review cards
   only when an explicit backend supplies them. The Review Radar contract must
   still produce useful cards without these fields.

   Alternative considered: make elaborated extraction mandatory for Review Radar.
   That would increase setup cost and make simple PR review less portable.

5. CI failure behavior is opt-in and severity-gated.

   Review Radar should default to producing cards and JSON. A CI mode can fail
   only on configured severe regressions such as missing required source hashes,
   unsupported high-confidence evidence joins, or explicitly configured import
   pressure thresholds.

   Alternative considered: fail on every high score. Review priority is routing
   context, not proof of bad code.

## Risks / Trade-offs

- [Risk] Semantic classifications can overclaim intent, especially
  "strengthened" and "weakened" conclusions. -> Mitigation: mark such classes as
  heuristic unless an elaborated backend supplies normalized theorem type
  evidence; include raw before/after surfaces for reviewer inspection.
- [Risk] Review scores become perceived quality grades. -> Mitigation: name them
  review priority or pressure, include contributing factors, and document that a
  high score can identify intentional shared foundations.
- [Risk] Before/after extraction can be slow on large Lean repos. -> Mitigation:
  cache by source/helper content, report phase timings, and start with selected
  roots before repo-wide runs.
- [Risk] Optional ProofIR and future x-ray rows can blur authority. ->
  Mitigation: keep namespaces separate (`proofir.*`, `xray.*`) and attach
  quoted-only/nonclaim text to reviewer cards.
- [Risk] Diff orchestration across git refs can become platform-specific. ->
  Mitigation: allow callers to pass prebuilt before/after report JSON first,
  then add convenience git-ref orchestration as a CLI layer.

## Migration Plan

1. Create child packets for a report/atlas-backed Review Radar MVP and semantic
   theorem-surface changelog fixtures.
2. Add structured diff report schema and Markdown reviewer-card rendering while
   keeping existing single-run reports unchanged.
3. Add CLI aliases after the schema stabilizes, preferably accepting both
   precomputed reports and repo refs.
4. Add optional x-ray fields only behind explicit backend labels and regression
   tests.
5. Archive this umbrella after child packets cover the MVP contracts and the
   nonclaim wording appears in docs/report examples.

Rollback is straightforward because the first implementation should be additive:
existing `ladon` reports, atlas exports, and ProofIR bridge behavior remain
valid if Review Radar output is disabled.

## Open Questions

- What exact theorem-surface normalization is acceptable before elaborated Lean
  extraction is available?
- Should `ladon diff` initially shell out to git, or should it require callers to
  provide before/after report paths until report contracts stabilize?
- Which import-pressure signals should be informational versus CI-failable?
- How much source text can reviewer cards include while keeping packets compact
  and source-first?
