## Why

The database work is useful only if ordinary Ladon commands can build, inspect,
and query it reproducibly. The final packet must prove the workflow survives
index replacement, remains bounded, and improves cross-evidence answers on real
ProofIR artifacts.

## What Changes

- Add ordinary CLI operations for configured ProofIR catalog status, theorem
  evidence, artifact evidence, and bounded obligation routes in text and JSON.
- Integrate configured artifact inputs into the atomic proof-search generation
  recipe and expose precise coverage/freshness states.
- Add end-to-end TDD fixtures for surface/replay joins, conditional CDC routes,
  duplicate declaration names, stale artifacts, unsupported kinds, and rebuilds.
- Calibrate on current Quux artifacts and record quality plus timing separately
  from portable correctness fixtures.
- Update README, CLI documentation, architecture documentation, and the
  authoritative Ladon skill without introducing caller-specific commands.

## Capabilities

### New Capabilities

- `ladon-proofir-cli-integration-and-calibration`: Installed operational
  workflow, stable renderers, rebuild safety, documentation, and evidence-based
  calibration for database-backed ProofIR queries.

### Modified Capabilities

None.

## Impact

- Extends installed CLI parsing/orchestration, result rendering, build inputs,
  docs, skills, integration tests, and release gates.
- Uses the existing project-local SQLite file and lock discipline; no second
  database or LLM-specific interface is added.
