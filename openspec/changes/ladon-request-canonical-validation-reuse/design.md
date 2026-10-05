# Design

## Context

See proposal.md for motivation. Dossier catalog validation owns a complete batch;
receipt processing subsequently validates each check and its environment/check
pair again. Those narrower reference scopes and per-receipt decisions remain.

## Goals / Non-Goals

**Goals:** Reuse canonical-owned immutable bytes for one request while preserving
all occurrence bounds, exact subset closure, complete off-page validation and
public raw entrypoints. Establish candidate-bound ordinary request cost.

**Non-Goals:** Persistent caching, receipt/context semantic caching, command/schema
changes, mathematical adoption, interface expansion or claims of reader benefit.

## Decisions

The canonical owner constructs a private population from raw occurrences through
existing preflight, reference and content validation. Preserve its original tuple
and encoded lengths, plus deduplicated lookup only after preflight. Immutable
member identity prevents substituting another request's object or caller copy.

An owner operation checks exact requested members, subset bounds and reference
closure against that subset alone. It never imports dependencies from the larger
catalog. Frozen traversal uses the same owner reference rules as raw traversal.
Private receipt/execution routes reuse this operation; all receipt and execution
semantics run as before. Public raw APIs continue independently validating.

Dossier preparation retains the population only while building the complete
receipt population. Rendering remains a projection over existing owned inputs.
No persistent object, cache or new public parameter is introduced.

## Risks / Trade-offs

- Full closure could conceal pair failure → schema-valid three-owner controls.
- Frozen traversal could omit references → equivalence and nested-reference tests.
- Copies or foreign handles could impersonate validation → exact member identity.
- Duplicate dedup could alter budgets/ambiguity → preserve original occurrences.
- Reuse might save little or increase memory → preselected ordinary installed gate:
  five alternating pairs per real inspect/guide, each median wall reduction ≥20%
  and faster in ≥4/5 pairs. Small regression is material above both 20% and 50ms;
  RSS regression above both 10% and 32MiB. Retain all samples and byte parity.
  Profile separately. Keep 32GiB cap. If safe reuse fails this gate, restore r65.

## Migration Plan

Characterize boundaries and freeze baseline before production edits. Integrate
root-owned changes, qualify shared canonical/receipt/SQLite/historical owners on
both supported Python minors, then measure installed candidates and independently
audit. Restore only this package's changes on failure; inherited work is retained.
