## Context

V3 must improve ordinary theorem workflows while preserving Ladon's caller-neutral CLI and authority boundaries.

## Goals / Non-Goals

**Goals:** integrate dossiers, triage, search/planning, native-v3 diagnostics, documentation, skills, and real-project calibration.

**Non-Goals:** hidden model-only commands, implicit refresh, modifying target Lean sources, or legacy conversion.

## Decisions

1. Existing CLI nouns remain; schemas version when semantics change.
2. Legacy ProofIR kinds fail with stable diagnostics and never reach semantic consumers or SQLite rows.
3. Dossiers separate claims, observations, derivations, attachments, coverage, and navigation views.
4. Lean-backed checking remains explicit, supervised, bounded, and represented as check-run observations.
5. Release gates use portable fixtures first, then Matrix-Factorization calibration. Quux is never inspected, executed, imported, or used for calibration.
6. Local users regenerate native-v3 artifacts and rebuild disposable databases; no data migration is attempted.

## Risks / Trade-offs

- [Stale local artifacts confuse users] → report the exact unsupported legacy kind and the regeneration command without interpreting its payload.
- [External calibration changes state] → default read-only and require explicit disposable-index rebuild authorization.

## Migration Plan

Delete legacy routes, ship native-v3 queries, update docs/skills, rebuild disposable indexes, calibrate, and make the native contract the only ProofIR surface.

## Open Questions

- None.
