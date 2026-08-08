## Context

Stored shapes reduce candidates but only Lean can elaborate patterns and decide candidate application under the active environment.

## Goals / Non-Goals

**Goals:** one elaboration plus one batched check request, explicit matching passes, substitutions, residual/unresolved separation, stale evidence, and finite limits.

**Non-Goals:** Python unification, implicit repository rebuilds, or multi-step adapter planning.

## Decisions

1. Add `elaborate-pattern` and `check-candidates` operations to `ladon-lean-semantic-v1`.
2. Run syntactic, definitional-reducible, symmetry, and optional bounded semi-reducible passes in declared order.
3. Open candidate binders with metavariables, synthesize instances under limits, and return unassigned proof, instance, and term goals separately.
4. Missing current-environment candidates remain explicit stale rows.

## Risks / Trade-offs

- [Environment startup dominates] → batch all candidates and measure phases separately.
- [Expensive unification] → per-request heartbeats, recursion, candidate, time, and output caps.
