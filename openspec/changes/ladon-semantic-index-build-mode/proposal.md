## Why

Semantic extraction is useful only when reusable module artifacts can be assembled into a validated generation without risking the prior published database.

## What Changes

- Add explicit `lexical`, `semantic`, and `hybrid` build modes, keeping omitted mode lexical during compatibility.
- Cache sound per-module semantic artifacts and assemble a fresh SQLite generation.
- Gate publication on schema, FK, integrity, coverage, query-plan, size, and optimization checks.
- Preserve previous generations after interruption or validation failure.

## Capabilities

### New Capabilities

- `ladon-semantic-index-build-mode`: Cached semantic generation construction with atomic publication and per-module coverage.

### Modified Capabilities

## Impact

Changes proof-search build/status orchestration, cache keys, locks, temporary database assembly, coverage output, CLI options, and failure-injection tests.
