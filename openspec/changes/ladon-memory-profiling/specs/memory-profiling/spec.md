## ADDED Requirements

### Requirement: External memory profiling recipe
Ladon SHALL document how to profile Python allocations using external Memray and
observe Python/Lean/Lake process memory using psutil, without requiring a new Ladon
module or changing normal runtime dependencies.

#### Scenario: Python allocation report
- **WHEN** an internal user follows the Memray recipe in the selected Ladon environment
- **THEN** they can produce an allocation capture and inspect a report without confusing
  its scope with separately executed Lean binaries

#### Scenario: Process memory observations
- **WHEN** a real Ladon operation is sampled with psutil
- **THEN** evidence distinguishes root and descendant readings, RSS and PSS/USS, unavailable
  measurements, finite sampling and instrumentation overhead

### Requirement: Qualification evidence and limits
The recipe SHALL be qualified against a bounded read-only Ladon operation, preserve
its result, record package/source identity, and distinguish one-off observations from
performance benchmarks or exact memory accounting.

#### Scenario: Qualified local exercise
- **WHEN** an exercise completes
- **THEN** the report records commands, scope, versions, outcomes and remaining gaps;
  a successful query is not evidence of complete process-tree or allocation coverage
