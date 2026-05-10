# Design

## Candidate Detection

For each repeated declaration suffix family, compare declaration pairs using:

- Jaccard overlap of resolved reference sets;
- weighted Jaccard overlap of unresolved-reference classification profiles;
- declaration kind equality when both kinds are known;
- fan-out delta.

The first implementation emits a candidate when the best pair has a reference
or unresolved-profile overlap at or above `0.75`.

## Report Boundary

The text report says "similar proof-family candidate". This is a review target,
not a proof that code was duplicated or should be refactored.
