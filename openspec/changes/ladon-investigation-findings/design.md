# Design

## Context

See proposal.md and the preserved retest-6 retrospective. `investigation.assess`
omits resolved legacy discrepancies; v2 additionally has arithmetic derivation
findings; v3 has immutable native bundles and sanitized reviews but no observation
capture without ProofIR. Progress-v1 receipts rebuild exact status dictionaries.

## Goals / Non-Goals

Preserve attributed evidence through public CLI capture, review and reporting.
No automatic semantic classifier, new mathematical proof, extraction expansion,
historical evidence rewrite or further blind audit is included.

## Decisions

Use an additive optional `observations` collection on existing plan versions.
Each entry binds an immutable record digest, source span, authored comparison,
formal-source spans, dependencies and append-only first/corrected responses.
Reuse the current response enums and exact challenge binding; sanitized observation
challenges exclude candidate verdicts. Capture validates sources but establishes
no proposition. Pending observations enter the ordinary queue. New public commands
are `observe`, `inspect-observations` and repeatable-input `report`; existing
challenge/ingest/reconcile commands dispatch observation subjects as appropriate.

Add a versioned finding projection to statuses. Legacy discrepancy judgments,
native reviewed subjects and observations retain their distinct authority.
Resolved method differences are findings, not perpetual blockers. Preserve
v2 scalar derivation findings alongside them. Observation-only v3 completion
permits recorded work completion with incomplete formal correspondence.
Coverage reports surveyed units separately from reviewed claims/observations;
it never asserts semantic inventory completeness.

Reports consume 1–16 compatible plans with identical scope/start/budget and at
most 128 MiB canonical combined input. They are read-only aggregate views, not
merged mutable plans or terminal receipts. Findings/observations retain originating
plan IDs. Identical repeated records deduplicate; divergent immutable payloads
reject; conflicting effective reviews remain visible across branches. Combined
collections are bounded at 4096. Branch queues/statuses remain visible rather
than allowing a resolved sibling to erase pending work.

New progress receipts use `ladon-investigation-progress-v2`. A dedicated historical
projection reconstructs v1 receipts without newly added finding/coverage fields,
while preserving old v2 derivation findings and old native bundle projections.
Exact source, plan, clock and receipt digests are still verified. No old bytes
are migrated. Corrections retain the original reviewer label; attribution is
still authored and not authenticated identity.

## Risks / Trade-offs

- Authored observations can omit real claims: expose survey/argument boundaries;
  no automatic completeness claim.
- New projections can invalidate old receipts: freeze a historical receipt fixture
  before production edits and test old/new replay and mutation rejection.
- Supplementary branches can hide disagreement: retain per-branch status and all
  original/corrected responses; reject identity collisions and clock changes.
- Labels can look like proofs: explicit `mathematicalFalsity: not-established`,
  absent bridge/support dimensions and no-checker authority throughout.

## Migration Plan

Existing plans require no edits. New observation fields are optional, new commands
are additive, and historical receipts keep their original reader. Rollback is a
reversible source patch; do not downgrade newly authored observation-bearing
plans to tooling that lacks their reader.
