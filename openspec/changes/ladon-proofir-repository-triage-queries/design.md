## Context

The normalized database contains enough relations to find evidence-health problems repository-wide, but current queries require a known theorem or artifact selector.

## Goals / Non-Goals

**Goals:** bounded SQL-first finding families, stable reason codes, actionable ownership/source anchors, deterministic severity inputs, and coverage.

**Non-Goals:** automatic proof repair, theorem correctness scoring, or opaque ML ranking.

## Decisions

1. Each triage family is an explicit SQL predicate with a stable rule ID. A generic query language was rejected for the alpha.
2. Initial families are unattached surface, ambiguous candidates, stale attachment, replay missing/stale/failed, conditional conclusion, stale/unmatched witness, unsupported/malformed artifact, and declaration-disconnected evidence.
3. Findings contain evidence facts and deterministic priority inputs; rendering may group them but cannot invent severity from authority.
4. Query caps apply per family and globally. Counts disclose truncated populations.
5. Owners come from exact source paths/declarations only; basename/module proximity is shown as context at most.

## Risks / Trade-offs

- [Large repositories produce many rows] → indexed predicates, family caps, and summary-first output.
- [Conditional evidence can be legitimate] → findings describe review need, not defects.
- [Duplicate symptoms] → stable deduplication keys and cross-reference related rule IDs.

## Migration Plan

Ship the query service and JSON schema first, then expose it through the ordinary CLI after installed-contract tests pass.
