## Why

`explain` currently compares two raw strings and rejects a theorem whose peeled conclusion exactly matches the requested goal. It should expose residual premises without pretending Python has Lean elaboration authority.

## What Changes

- Resolve bounded candidate signatures from the fresh index and peel stored binders.
- Normalize lexical representation consistently with type search.
- Return unmatched premises as residual goals and reserve negative classification for established mismatch.
- Use `indeterminate-lexical` when parsing or normalization cannot decide.

## Capabilities

### New Capabilities

- `ladon-binder-aware-proof-difference`: Conservative binder peeling, normalized conclusion comparison, and residual-premise reporting.

### Modified Capabilities

## Impact

Changes proof-difference analysis, CLI candidate resolution, result schemas, fixtures, and authority documentation.
