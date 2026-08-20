## Why

Complete semantic index rows cannot be inferred safely from pretty-printed Lean text; Ladon needs a supervised, versioned Lean-owned extraction boundary.

## What Changes

- Add the `ladon-lean-semantic-v1` framed NDJSON protocol with request IDs and ordered chunk frames.
- Extract module-owned declarations, complete binders/dependencies, structures, fields, and versioned expression fingerprints.
- Validate terminal counts, duplicates, frame order, partial streams, deadlines, cancellation, and process cleanup.

## Capabilities

### New Capabilities

- `ladon-lean-semantic-extraction-protocol`: Lean-owned semantic extraction with explicit completeness and bounded transport.

### Modified Capabilities

## Impact

Adds Python protocol/runtime modules, a Lean index helper, cache identities, compact integration fixtures, and supervisor failure tests.
