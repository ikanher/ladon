# Child 4: Witness Packet Evidence Gate

## Literature Basis

- `arxiv:2205.07535` Code smells via modern code review.
- `arxiv:2306.01377` Code smells datasets and validation mechanisms.
- `arxiv:2602.18270` Static analyzer false-positive caution.
- `openreview:proofgym-2025` ProofGym.

## Problem

Ladon was originally useful for packet review and witness evidence, but that
surface was removed from the clean core. Rebuilding it should follow the
literature: evidence and validation must accompany analyzer claims.

## Proposed First Slice

Add a packet/witness evidence checker that inspects a packet directory for:

- manifest or metadata;
- witness JSON artifacts;
- independent checker scripts;
- positive and negative tests;
- commands run;
- source/proof owner references.

This should produce an evidence completeness score, not correctness claims.

## Acceptance Bar

- Tests over tiny synthetic packet directories.
- JSON/text report fields.
- No dependency on matrix-factorization-specific paths.
- Smoke run against one existing review-data directory in `temp/`.
