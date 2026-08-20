## Context

Matrix-Factorization smoke runs showed that common-layer candidates matter
beyond direct policy violations. Facades also need separate treatment so public
aggregation does not look like implementation coupling.

## Goals / Non-Goals

**Goals:**

- Rank common dependencies across multiple configured groups.
- Separate facade subtypes from implementation fan-out.
- Add negative fixtures for intentional shared foundations.

**Non-Goals:**

- No automatic layer extraction.
- No claim that high fan-in is inherently bad.

## Decisions

- Use policy groups and source-shape metadata, not project names.
- Report confidence, group count, importer count, and samples.

## Risks / Trade-offs

- Intentional foundations can be overflagged -> Add allow/exclusion policy
  tests and negative fixtures.
