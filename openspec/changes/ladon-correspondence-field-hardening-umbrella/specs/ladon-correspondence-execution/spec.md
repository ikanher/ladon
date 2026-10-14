## Purpose

Make local correspondence replay measurable and economical while retaining exact per-obligation checking, freshness, trust, and bounded evidence delivery.

## ADDED Requirements

### Requirement: Stage costs and populations are observable
Public correspondence checks SHALL report stage timing, process counts, resource bounds, observed memory scope, and input/output sizes. Distinct prose claims, repeated checks, typing probes, and substantive obligations SHALL be counted separately. Overlapping durations SHALL NOT be added as exclusive wall time.

#### Scenario: Concurrent build affects measurement
- **WHEN** a check overlaps an external build or setup activity
- **THEN** the measurement discloses that overlap and cannot alone establish a checker regression or speedup

### Requirement: Request-local reuse preserves checking authority
Shared preparation within one request SHALL retain exact per-goal terms, contexts, outcomes, independent compiler checks, and trust coverage. It SHALL verify bound source and environment stability before and after the request. Earlier stored success SHALL NOT replace fresh checking.

#### Scenario: One goal fails in a batch
- **WHEN** one term is rejected while another is accepted in shared preparation
- **THEN** each result retains its own evidence and the failed term cannot contaminate or certify its sibling

#### Scenario: Mid-request input mutation
- **WHEN** a bound source, helper, compiled import or sidecar changes during shared work
- **THEN** affected acceptance is withheld and no cached success masks the change

#### Scenario: Bounded interruption
- **WHEN** an execution limit interrupts a group of obligations
- **THEN** unattempted obligations remain explicit and process cleanup retains the declared supervisor guarantees

### Requirement: Compact delivery preserves complete evidence
Ordinary native output SHALL avoid unnecessary serialization expansion without dropping obligations, first responses, provenance, or diagnostics. Equivalent compact and formatted representations SHALL preserve parsed content and canonical identity. Existing input/output caps SHALL remain enforced.

#### Scenario: Formatting causes input overflow
- **WHEN** a complete payload fits the input cap compactly but exceeds it with whitespace
- **THEN** the public producer provides the complete compact representation without requiring manual evidence editing

#### Scenario: Complete compact payload is still too large
- **WHEN** compact content exceeds the configured limit
- **THEN** the operation returns a bounded explicit failure instead of truncating semantic evidence or silently raising the cap

### Requirement: Performance claims use equivalent measured work
An operational improvement claim SHALL compare frozen semantically equivalent subjects and required checks under matched environment, cache, concurrency, and resource policies. The qualification report SHALL include paired trials, failures, medians, and declared target disposition. A correctness loss SHALL invalidate any claimed speedup.

#### Scenario: A pre-fix unsupported case becomes supported
- **WHEN** old code omits a transfer that new code actually checks
- **THEN** its shorter old runtime is not treated as a successful equivalent baseline; correctness repair and optimization are measured separately
