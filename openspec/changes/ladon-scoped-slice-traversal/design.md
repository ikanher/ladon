# Design

## Context

The helper enumerates every exact-head application and Python validates and replays the whole frame. The original theorem needs 109,620 traversal visits for one application; the old public allowance is 8,192. The user requested configurable allowances and performance measurement before optimization.

## Goals / Non-Goals

Make traversal allowance explicit without changing ordering, scope, premise accounting, exhaustive enumeration or public receipt shape. Do not infer mathematical validity from extraction, expand the contract producer, or turn an informed case into a discovery benchmark.

## Decisions

Use default 131,072 (the next power of two above measured traversal), accepted range 1–1,048,576. Validate strict integer inputs before repository resolution. Thread the value through a numeric Lean command argument for both helpers, store it in `limits.nodes`, and preserve it at both correspondence replay sites. Existing slice identity already includes limits; bind the shared validation module into checker implementation identity. Private helper defaults are not public policy: every extraction supplies its chosen allowance explicitly.

Keep 60-second process time, 12-GiB process-tree RSS, 8-MiB output, depth 64, and serialized-expression limits independent. Higher node allowance cannot bypass those guards. Preserve historical receipts without upgrading their authority.

Keep the original traversal. A three-pair experiment at equal allowance measured cache traversal medians of 25 ms versus 98 ms, but total helper-process medians of 1.39 s versus 1.45 s and essentially unchanged memory. This modest end-to-end gain does not warrant the added cache now. Preserve the proposed negative-cache implementation and regression as deferred evidence only.

### Closed proof instance binders

The pinned Lean printer can omit a lambda instance name when it is absent from
the final body, even though later binder types refer to that name. Use a local
lambda-telescope delaborator for closed proof text, explicitly preserving names,
types and all four binder kinds. It delegates the non-lambda body to Lean's
printer and changes no expression or global delaborator registration. Shared
printer material is composed into the two slice helpers and the source-goal
completion helper, and bound to their helper digests and the checker implementation
identity. Slice consumers retain the 64-level telescope limit; completion uses
Lean's configured recursion limit rather than inheriting that slice-only limit.
Keep the empty-context
parse/elaboration, unresolved-metavariable rejection, proof/type equality and
resource checks. Nested-body limitations continue to fail closed if encountered.

## Risks / Trade-offs

- Larger allowance can expose another failure → run the actual consumer within unchanged independent bounds and report the next frontier without claiming completion.
- Explicit budget forgotten during replay → real end-to-end regression records both freshness calls with a nondefault allowance.
- New validation can affect imported historical slices → existing valid 8,192 allowances remain accepted; current replay still checks helper identity.
- Measurement scope → the comparison measures traversal/helper startup on this theorem, not complete serialization or general workloads.

## Migration Plan

Add the CLI/API option with no schema migration. Old valid budgets remain representable. Roll back the reversible patch if necessary; no deployment or push. Run affected contracts and independent integrated review, preserving broader qualification gates.
