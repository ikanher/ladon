## Context

Catalog and semantic tables record many failure states, but query results often collapse them to empty arrays. Absence must be tied to a known search population and generation to be meaningful.

## Goals / Non-Goals

**Goals:** model configured/unconfigured, observed/absent, unsupported, malformed, stale, ambiguous, unmatched, context-only, and unavailable states independently for every evidence family.

**Non-Goals:** closed-world claims about theorem truth or automatic remediation.

## Decisions

1. Coverage is a matrix keyed by evidence family, with `configuration`, `availability`, `population`, `matched`, `state`, and bounded reasons.
2. Negative evidence is emitted only when a relevant population was actually inspected. Unconfigured and unavailable never become `absent`.
3. Staleness, ambiguity, failure, and absence remain independent flags; a successful replay does not clear a stale attachment.
4. Rebuilds recompute coverage from the unpublished generation. Query-time coverage may add selector-specific facts but cannot rewrite stored state.
5. Context-only evidence explicitly names why it was not attached to the theorem.

## Risks / Trade-offs

- [Many states can confuse users] → stable vocabulary plus compact text explanations.
- [Counts drift from rows] → derive both from the same SQL predicates and test equality.
- [Negative evidence is overread] → mandatory nonclaims explain the open-world boundary.

## Migration Plan

Add coverage dictionaries without removing existing arrays, update dossier and triage callers, then make coverage mandatory in the next result schema only.
