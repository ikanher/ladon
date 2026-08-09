## Why

`consumers` reports `complete` with zero dependency rows, and `constructor` reports `available` even though the CLI supplies no indexed fields. Empty results must distinguish genuine absence from unavailable semantic coverage.

## What Changes

- Derive response status from generation coverage and the selected population.
- Wire constructor queries to stored structures and fields instead of an empty tuple.
- Distinguish known empty structures from unextracted field populations.
- Include population, authority, omissions, and truncation in both result contracts.

## Capabilities

### New Capabilities

- `ladon-coverage-sensitive-consumers-and-constructors`: Coverage-honest reverse-consumer and structure-field results.

### Modified Capabilities

## Impact

Changes consumer/constructor SQL and handlers, public versioned results, tests, docs, and compatibility handling.
