## Why

The atlas is Ladon's most product-shaped surface: it can show what changed,
what recurs, what is hot, which evidence packets are incomplete, and which
ProofIR joins need scrutiny. The next step is to make that a coherent reviewer
workflow instead of separate scripts and report fragments.

## What Changes

- Define an atlas-first review workflow over generated Ladon reports.
- Extend reviewer cards to combine root identity, backend, findings, review
  regions, strongest evidence, known non-claims, packet evidence, and optional
  ProofIR diagnostics.
- Keep ProofIR diagnostics optional and namespaced under `proofir.*`.
- Preserve JSON/SQLite/diff outputs as the machine-readable foundation.

## Capabilities

### New Capabilities

- `ladon-atlas-review-workflow`: Defines atlas-first reviewer workflow outputs,
  bridge-aware cards, and query/diff questions.

### Modified Capabilities

None.

## Impact

- Affected code: `src/ladon/atlas.py`, `src/ladon/atlas_sqlite.py`,
  `src/ladon/atlas_diff.py`, `src/ladon/proofir_bridge.py`, atlas scripts, and
  tests.
- Affected outputs: atlas JSON, Markdown summaries, SQLite exports, diff
  reports, and reviewer cards.
- Affected workflow: reviewers should start from atlas cards or queries instead
  of raw per-root JSON.
