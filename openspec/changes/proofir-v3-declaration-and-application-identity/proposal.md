## Why

The alpha worker uses structural type fingerprints as declaration identity, so distinct declarations with the same type can collide. It also records residual candidate application acceptance against the goal statement, which can make an unproved goal look accepted.

## What Changes

- Separate declaration, statement/type, optional value/proof, and candidate-application subjects.
- Require exact qualified declaration identity for exact attachment.
- Attach residual application checks to an application or step subject while leaving the goal statement unchecked.

## Capabilities

### New Capabilities
- `proofir-v3-declaration-and-application-identity`

### Modified Capabilities

## Impact

Changes semantic-worker subjects, attachment ranking, check-run results, typed references, SQLite subject rows, and search-versus-identity documentation.
