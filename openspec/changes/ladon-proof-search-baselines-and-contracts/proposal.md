## Why

Semantic proof-search changes need reproducible contract and performance evidence before implementation so regressions and known failures are measurable rather than anecdotal.

## What Changes

- Add public JSON contract fixtures and regression fixtures for mixed-case and exact-name refinement.
- Add benchmark and SQL trace-count utilities for build, query, route, startup, database-size, and RSS measurements.
- Record current expected failures without blessing incorrect behavior.

## Capabilities

### New Capabilities

- `ladon-proof-search-baselines-and-contracts`: Repeatable correctness and performance baselines for the proof-engineering program.

### Modified Capabilities

## Impact

Adds test fixtures, benchmark harnesses, trace helpers, and checked-in baseline metadata; it does not change production query semantics.
