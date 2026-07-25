## Why

Ladon is useful enough to become shared infrastructure, but its current
orchestration is still too monolithic to evolve safely. Before deeper analysis
work or a Rust port, we need explicit pipeline seams, stable timing surfaces,
and TDD coverage around those seams.

## What Changes

- Add a pipeline architecture capability for named execution phases and a
  structured run context/result boundary.
- Add stable timing and counter keys for the major Ladon phases.
- Add adapter coverage so legacy module extraction can feed the new pure
  analysis kernels without duplicating graph logic.
- Add small fixtures and tests that assert phase shape, not noisy wall-clock
  values.
- Keep current CLI behavior compatible; new report fields are additive.

## Capabilities

### New Capabilities

- `ladon-pipeline`: Defines Ladon's named pipeline phases, run context, stable
  phase timing surface, and compatibility expectations for CLI/report output.

### Modified Capabilities

- None.

## Impact

- Affected code: `src/ladon/`, especially CLI orchestration, legacy extraction
  adapters, and analysis module wiring.
- Affected tests: `tests/`, with new pipeline fixture and timing-shape tests.
- Affected reports: JSON/text reports may gain additive `pipeline` or
  `timings` fields, but existing consumers should keep working.
- Dependencies: no new required runtime dependency is expected for this packet.
