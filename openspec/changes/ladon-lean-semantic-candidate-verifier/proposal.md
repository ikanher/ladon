## Why

SQLite fingerprints can shortlist candidates but cannot decide Lean applicability, substitutions, type-class synthesis, or residual proof goals.

## What Changes

- Elaborate patterns and assumptions once in the requested Lean module environment.
- Batch candidate checking through syntactic, reducible, symmetry, and bounded semi-reducible passes.
- Return substitutions, residual proof premises, unresolved instances/terms, stale candidates, exact authority, bounds, and diagnostics.

## Capabilities

### New Capabilities

- `ladon-lean-semantic-candidate-verifier`: Batched Lean-authoritative pattern elaboration and candidate application evidence.

### Modified Capabilities

## Impact

Extends the semantic helper/protocol, Python result models, runtime supervision, and fixtures for wildcards, aliases, symmetry, coercions, instances, and failures.
