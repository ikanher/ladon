## Context

Static schema checks enumerate desired index names, but current production SQL includes full scans for selected attachments by declaration and diagnostics by artifact, plus fragile skip-scans for exact declarations and unaligned negative-evidence triage.

## Goals / Non-Goals

**Goals:** derive indexes from actual SQL, validate populated plans, cover foreign-key child operations, and keep sparse triage indexes compact.

**Non-Goals:** changing ProofIR authority, materializing theorem truth, or indexing every column combination.

## Decisions

1. Maintain a query-to-access-path registry next to schema validation with operation, predicate prefix, ordering need, expected relation, and accepted plan class.
2. Add direct indexes for `declarations(name)`, selected attachments by declaration, diagnostics by artifact, and DAG obligations.
3. Use partial indexes for rare stale/failed/unsupported states only after fixture selectivity measurement.
4. Audit foreign-key child leading columns separately from read queries because cascade enforcement has different access patterns.

## Risks / Trade-offs

- [More indexes increase base size] → each addition needs populated latency/plan evidence and net byte accounting.
- [Empty fixtures make any plan look cheap] → require nonempty, skewed representative populations.

## Migration Plan

Land failing plan tests, add or reshape one index family at a time, bump schema generation through the rightsizing packet, and rebuild disposable databases.

## Open Questions

- Which negative-state indexes remain worthwhile after real ProofIR population calibration.
