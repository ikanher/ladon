## Context

Ladon already computes module DAG metadata, facade subtype, generated tags,
root closures, and declaration source evidence. This packet turns those rows
into a Lean module-readiness surface.

## Goals / Non-Goals

**Goals:**
- Report readiness pressure from existing evidence.
- Accept optional module-system witnesses with explicit authority metadata.
- Keep witness absence safe.

**Non-Goals:**
- Do not run Lean module-system checks by default.
- Do not treat namespace drift as a correctness error.
- Do not prove theorem truth.

## Decisions

- Use an additive `module_readiness` namespace in reports.
- Keep witness rows quoted and low-confidence if backend/version/command/hash
  metadata is missing.
- Derive namespace drift only when declaration evidence exists.

## Risks / Trade-offs

- Intentional namespace drift may be noisy; mitigate with role/policy metadata
  and review-only severity.
