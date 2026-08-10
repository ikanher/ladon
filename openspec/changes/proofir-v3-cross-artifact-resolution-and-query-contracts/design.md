## Context

The semantic worker emits a check-run artifact followed by a derivation or attempt that references it. One-item validation rejects this valid incremental flow, while the graph reader rejects external evidence references as though they were graph topology.

## Goals / Non-Goals

**Goals:** atomic incremental closure, typed external evidence resolution, truthful bounded query accounting, complete derivation records, and set-oriented query plans.

**Non-Goals:** following arbitrary remote artifacts, converting external checker links into proof premises, or reporting an unbounded total by default.

## Decisions

1. Projection validates against `persisted valid artifacts ∪ incoming batch` inside one transaction and publishes none of the batch on failure.
2. Premise/conclusion/step references define derivation topology; check-run and support references remain typed evidence links.
3. Every public limit is a positive bounded integer; invalid limits fail before SQL execution.
4. `matched` means an exact computed count only when the result says it is exact; otherwise use bounded lower-bound accounting.
5. Dossiers use set-oriented queries and include premise occurrences, conclusion, rule, context, and checker relationships for each returned step.

## Risks / Trade-offs

- [Existing database rows may be stale] → require their stored artifact validation state and content ID before using them for closure.
- [Exact counts are costly] → expose exact versus bounded count semantics explicitly rather than relabeling a prefix.

## Migration Plan

Add batch/incremental equivalence tests, introduce a resolver context backed by the transaction, repair topology classification, then replace per-subject loops and regenerate query fixtures.

## Open Questions

- None.
