## Context

FTS `any` ranking gives broad terms disproportionate influence, while architecture rendering includes repository-global candidate inventories even for a two-module owner graph. Both surfaces need bounded, inspectable defaults without hiding wider evidence.

## Goals / Non-Goals

**Goals:** rank concentrated basename evidence, expose contributions, bound broad matching, and focus owner reports by default.

**Non-Goals:** learned ranking, semantic applicability claims, deleting global integrity analysis, or changing raw JSON evidence without versioning.

## Decisions

1. Use a versioned generic-token table and deterministic ranking vector: exact/phrase, distinct specific basename segments, total distinct segments, ownership, source, stable name.
2. Derive default minimum matches from non-generic query length and expose an explicit override.
3. Split report projection from repository-global inventory rendering. Default owner output includes compact global counts and explicit omissions; a flag selects samples.
4. Measure result quality with named expected candidates and report volume with structural counts, not token estimates alone.

## Risks / Trade-offs

- [Stopword policy suppresses useful names] → expose contributions and broad override; version the policy.
- [Focused defaults surprise existing snapshot users] → version projection metadata and retain explicit global mode.

## Migration Plan

Land ranking/report failing fixtures, add new metadata and flags, update snapshots, then calibrate on Matrix-Factorization.

## Open Questions

- Whether the default minimum-match rule is `min(2, specific_terms)` or a ratio after calibration.
