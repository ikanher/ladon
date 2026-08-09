## Context

The source-map and SQLite attachment paths have drifted, and repository configuration can currently carry semantic links that neither artifact owns.

## Goals / Non-Goals

**Goals:** one resolver policy, retained candidates, explicit fallback boundaries, and attributable content-ID links.

**Non-Goals:** accepting name-only matches as attachments or making manifests canonical semantic authorities.

## Decisions

1. Resolver order is environment+declaration+fingerprint, producer declaration ref, content+range, content+name, path/range/name, module/name, then name-only diagnostic.
2. Selected observations retain all candidates, policy version, resolver identity, freshness, evidence, and rejection reasons.
3. Method names are mechanically consistent with tested predicates; a path/hash method requires a path match.
4. Artifact links live inside artifacts or separate link-observation artifacts over content IDs.
5. Repository configuration discovers roots only; compatibility links are labeled manifest assertions.
6. Resolver algorithms may be reimplemented from Quux research kernels, but production imports and test dependencies on Quux are forbidden.

## Risks / Trade-offs

- [Fewer optimistic attachments] → emit actionable ambiguity/unattached diagnostics.
- [Policy changes alter selections] → content-address the policy and retain decision records.

## Migration Plan

Freeze native candidate-selection vectors, correct method labels, then route source-map and SQLite projection through the shared resolver. No retired bridge adapter participates.

## Open Questions

- Whether source ranges require byte offsets, UTF-8 offsets, or both.
