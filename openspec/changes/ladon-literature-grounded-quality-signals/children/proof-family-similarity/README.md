# Child 3: Proof Family Similarity

## Literature Basis

- `arxiv:2306.16171` Source code similarity and clone detection SLR.
- `arxiv:2308.01191` LLM code clone detection survey.
- `arxiv:1810.11979` Formal proofs of Tarjan's algorithm across provers.
- `arxiv:2305.04369` Getting more out of LLMs for proofs.

## Problem

Current declaration family grouping uses only suffix names. It catches obvious
families but cannot distinguish harmless naming conventions from repeated proof
skeletons.

## Proposed First Slice

Extend declaration family rows with deterministic similarity features:

- shared suffix;
- shared reference-set overlap;
- shared unresolved-class profile;
- declaration kind;
- fan-out similarity.

Avoid LLMs in the first implementation. LLM explanation can sit on top later.

## Acceptance Bar

- Pure function over `LeanDeclaration` inventory and graph summary.
- Tests for high/low similarity synthetic families.
- Text report says "similar proof-family candidate", not "clone".
- Smoke report highlights BIFR `ge_one_add_firstLag`-style families.
