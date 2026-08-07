## Context

An unfinished Lean file may not build as a module, but Lean's frontend can expose
goals and context at an instrumented location. Probes must be isolated because query
work must not edit or import generated scratch content into production modules.

## Goals / Non-Goals

**Goals:** location-based goal/context capture, local-binder matching, compiler-error
queries, separate minimal examples, and supervised Lean confirmation.

**Non-Goals:** no editor protocol replacement, automatic insertion, tactic search, or
claim that a scratch probe proves the production theorem.

## Decisions

- Copy/instrument the requested scratch source in a temporary workspace tied to its
  source hash and use the pinned Lean environment to capture the selected goal.
- Return local declarations with binder info, types, values only when safe/available,
  namespace/open scopes, imports, and exact source position.
- Treat parsed compiler errors as user-supplied query evidence until re-elaborated.
- Generate a minimal `example` with explicit imports and hypotheses in a temporary
  artifact; compile it under the normal process supervisor and retain diagnostics.
- Never write the probe into the target repository or include it in default builds.

## Risks / Trade-offs

- [Position shifts during instrumentation] → Anchor by source hash and syntax range.
- [Initializers execute] → Apply the same trusted-repository warning and supervision
  as other Lean-backed operations.
- [Probe context differs from owner] → Record every import/open/hypothesis and keep the
  confirmation scoped to the probe.

## Migration Plan

Start with explicit scratch files and single goals; add compiler-error normalization
after location capture is stable. Temporary artifacts are disposable rollback state.
