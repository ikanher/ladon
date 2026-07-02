## Context

Ladon observes imports textually. Lean/Lake witnesses can quote minimized import
sets from build-aware tools. The two evidence classes must remain separate.

## Goals / Non-Goals

**Goals:**
- Normalize import-diet witness rows.
- Compare fresh witness rows to observed direct imports.
- Report source-located redundant-import candidates.

**Non-Goals:**
- Do not run `lake shake` by default.
- Do not automatically remove imports.
- Do not claim an import is safe to remove without replay.

## Decisions

- Use an optional `--import-diet-witness` CLI path.
- Treat missing witnesses as a skipped phase.
- Treat stale or malformed witnesses as diagnostics.

## Risks / Trade-offs

- Witnesses can drift from source; mitigate with source-hash and stale-row
  diagnostics.
