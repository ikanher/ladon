# Child Packet: ladon-atlas-review-workflow-and-bridge-cards

## Purpose

Make the atlas the reviewer entry point by unifying report diffs, SQLite
queries, reviewer cards, packet evidence, and optional ProofIR diagnostics.

## Expected Scope

- A single workflow that answers what changed, what recurs, which roots need
  review first, which joins are low-confidence, and which packets are incomplete
  or stale.
- Reviewer cards that include root, backend, top findings, review regions,
  strongest evidence, known non-claims, and optional ProofIR diagnostics.
- SQLite/canned query coverage for recurring hotspots and proof/evidence
  pressure.
- Bridge diagnostics remain optional and namespaced under `proofir.*`.

## Non-Goals

- No web UI.
- No graph database dependency.
- No LLM-generated explanations.
- No promotion of ProofIR or packet evidence into theorem truth.
