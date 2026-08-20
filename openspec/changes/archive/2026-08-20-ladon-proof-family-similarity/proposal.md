# Ladon Proof Family Similarity

## Why

Declaration-name families are useful, but suffix grouping alone is crude. It
cannot tell whether a family is just naming convention or whether two
declarations share proof/reference structure.

The clone/similarity literature supports adding deterministic similarity
features before any LLM explanation layer.

## What

- Add proof-family similarity candidates to declaration graph summaries.
- Use shared suffix, resolved reference overlap, unresolved-class profile
  overlap, kind match, and fan-out delta.
- Render candidates as "similar proof-family candidate", not "clone".

## Non-Goals

- No semantic equivalence claim.
- No proof clone claim.
- No LLM-based similarity.
