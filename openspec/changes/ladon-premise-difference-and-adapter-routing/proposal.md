## Why

A candidate theorem that nearly applies is often more useful than a lexical match,
but Lean errors do not provide a durable proof route. Ladon should explain the exact
unmatched premises and existing bridges without claiming its suggestions compile.

## What Changes

- Compare an elaborated goal and local context with a candidate declaration and
  report binder substitutions, discharged premises, and unmatched premises.
- Classify common mismatches: inequalities, all-state versus almost-everywhere,
  measurability strength, equality orientation, maps, aliases, representations, and
  index/range boundaries.
- Find indexed declarations that may discharge each unmatched premise.
- Maintain a versioned advisory adapter catalog with exact side conditions and
  source declarations for common Lean/Mathlib proof moves.
- Emit machine-readable accepted/rejected proof-route cards.

## Capabilities

### New Capabilities

- `ladon-premise-difference-and-adapter-routing`: Lean-backed candidate difference
  analysis, premise routing, and side-condition-complete advisory adapters.

### Modified Capabilities

None.

## Impact

- Adds candidate-application helper operations, mismatch taxonomy, adapter registry,
  route-card schema, CLI rendering, and positive/negative semantic fixtures.
