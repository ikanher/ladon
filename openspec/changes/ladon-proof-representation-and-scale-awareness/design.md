## Context

Representation and range semantics are domain-specific. Ladon can validate policy
shape and join named transports to Lean declarations, but cannot infer that a scale
law or uniformity claim is mathematically appropriate from names alone.

## Goals / Non-Goals

**Goals:** validated representation-pair policy, exact transport joins, scale and
fixed/window/unbounded range classifications, and route-card warnings.

**Non-Goals:** no hard-coded project terms, symbolic asymptotic solver, or theorem
truth assigned to policy prose.

## Decisions

- Policy declares stable representation IDs, type-pattern anchors, direction,
  transport declaration names, scale expressions, and range classes.
- A transport is Lean-confirmed only when its indexed/elaborated type matches the
  declared relation; otherwise policy status is unresolved or invalid.
- Difference analysis can attach representation/range diagnostics but cannot hide
  the original unmatched types or premises.
- Uniformity classifications are explicit: fixed index, finite-window uniform with
  bound parameter, or unbounded-family uniform. Unknown stays unknown.
- Scale warnings show both normalized and requested expressions and any parameter
  growth; they never cancel factors textually without Lean evidence.

## Risks / Trade-offs

- [Policy becomes verbose] → Provide examples and reusable schema, not built-in names.
- [Equivalent arithmetic is missed] → Start conservative and integrate only bounded
  Lean normalization routes.
- [False uniformity] → Require explicit range class and retain parameters.

## Migration Plan

Add policy as optional advisory input. Invalid policy is an invocation error; absent
policy leaves search unchanged. Removing it is a clean rollback.
