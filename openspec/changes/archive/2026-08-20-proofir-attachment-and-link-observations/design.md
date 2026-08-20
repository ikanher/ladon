## Context

Source attachment proves reference alignment, not theorem validity.

## Goals / Non-Goals

**Goals:** one policy, truthful method labels, ambiguity retention, diagnostic name-only matches, and attributable links.

**Non-Goals:** treating source identity or manifest relationships as proof authority.

## Decisions

1. Stronger environment/fingerprint evidence precedes source/path fallbacks.
2. Ambiguous strongest-tier candidates remain inspectable and unselected.
3. Manifest-only links are assertions, not canonical semantic linkage.

## Risks / Trade-offs

- [Candidate retention increases storage] → enforce finite resolver caps and normalize the projection.

## Migration Plan

Regenerate native attachment/link observations and discard compatibility rows.

## Open Questions

- None.
