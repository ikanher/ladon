## ADDED Requirements

### Requirement: Portable large-inventory fixture
The required benchmark suite SHALL generate a deterministic, target-neutral
Lean repository from a versioned manifest with at least 2,600 modules,
1,500,000 source lines, and 100,000 lexical declaration candidates. The fixture
MUST include handwritten-looking modules, explicitly generated families, deep
namespaces, facade modules, shared dependencies, and owner roots without
depending on a sibling checkout or network access.

#### Scenario: Required clean-checkout gate
- **WHEN** the large-inventory benchmark runs from an installed candidate in a tracked-only export
- **THEN** it generates the manifest-defined repository in disposable storage and measures the ordinary public CLI without reading a maintainer-local Lean repository

#### Scenario: Deterministic fixture regeneration
- **WHEN** two benchmark runs use the same fixture manifest, seed, and generator version
- **THEN** their generated source-path inventory and content hashes are identical

### Requirement: Explicit cold resource ceilings
The portable large-inventory text analysis gate SHALL enforce ceilings of 20
seconds cold wall time, 512 MiB peak resident memory, 32,000,000 canonical JSON
bytes, and 500,000 compact text bytes on the required Linux reference job. The
gate MUST report each measurement separately and MUST NOT combine them into an
aggregate score.

#### Scenario: Cold run within budget
- **WHEN** the generated large inventory is analyzed with an empty analysis cache
- **THEN** the installed CLI completes within every cold ceiling and the benchmark records wall time, peak RSS, JSON bytes, text bytes, module count, source-line count, and declaration-candidate count

#### Scenario: One resource ceiling is exceeded
- **WHEN** any cold wall-time, RSS, JSON-size, or text-size measurement exceeds its committed ceiling
- **THEN** the required gate fails and identifies the exceeded metric, observed value, ceiling, candidate identity, and fixture-manifest identity

### Requirement: Measured warm reuse
An unchanged warm analysis using an explicit cache directory SHALL complete
within 5 seconds on the required Linux reference job, SHALL remain within the
512 MiB peak-RSS ceiling, and SHALL produce byte-identical normalized report
content. Warm success MUST include a validated cache hit rather than merely a
faster elapsed time.

#### Scenario: Unchanged warm run
- **WHEN** the same installed candidate analyzes the same generated repository with equal analysis options and a valid cold-run cache
- **THEN** the run records cache hits, completes within the warm ceilings, and emits normalized report bytes equal to the cold run

#### Scenario: Relevant source changes
- **WHEN** one generated source or another registered fingerprint input changes before the warm run
- **THEN** Ladon invalidates the affected reusable unit, preserves valid unaffected units, and MUST NOT report the changed unit as a cache hit

### Requirement: Versioned text-analysis cache
Reusable text discovery and indexing SHALL adopt the existing versioned cache
outcome and fingerprint vocabulary used by the Lean runtime contract. A cache
fingerprint MUST cover analyzer and schema identity, source-layout identity,
source content, relevant policy and scope options, and every derived artifact
that is reused.

#### Scenario: Unfingerprintable reusable input
- **WHEN** Ladon cannot establish a strong fingerprint for a discovery or indexing input
- **THEN** it records a cache bypass with a reason and recomputes the unit instead of claiming a sound hit

#### Scenario: Interrupted cache write
- **WHEN** analysis is cancelled or fails while a reusable unit is being produced
- **THEN** no incomplete cache entry is committed and an earlier valid entry remains readable

### Requirement: Single canonical payload ownership
Each phase or capability payload SHALL have exactly one canonical location in a
serialized report. Phase-status and timing projections MUST contain only their
envelope fields, scalar summaries, or explicit references to the canonical
payload and MUST NOT embed a second copy of that payload.

#### Scenario: Module-DAG serialization
- **WHEN** a report contains module metadata, import sites, edges, and lexical declaration evidence
- **THEN** those rows occur under one canonical module-DAG owner and neither the phase envelope nor pipeline timing projection repeats them

#### Scenario: Payload-ownership audit
- **WHEN** the required report-contract gate traverses a canonical report
- **THEN** every registered payload owner resolves uniquely and no compatibility projection contains a structurally equal full-payload copy

### Requirement: Bounded report-contract migration
Scale-driven removal of duplicated report locations SHALL follow the existing
report-version and reader-dispatch contract. If the ownership change is
incompatible with report v2, Ladon MUST introduce a new report major with a
documented bounded adapter instead of silently changing v2 field meaning.

#### Scenario: Explicit compatibility serialization
- **WHEN** a caller requests a supported older report major during its documented compatibility window
- **THEN** Ladon uses an explicit serializer, identifies information or scale costs, and leaves the canonical current-major ownership invariant unchanged

#### Scenario: Unsupported old consumer
- **WHEN** a reader receives a report major whose compatibility window has ended
- **THEN** it returns the existing actionable unsupported-version diagnostic rather than guessing duplicated or canonical payload locations

### Requirement: Streaming and bounded construction
Ladon MUST construct discovery, typed reports, text rendering, and JSON
serialization without retaining multiple full-size copies of the source
inventory or serialized report. JSON file output SHALL be written through a
bounded or streaming path and MUST NOT require a second report-sized decoded
string.

#### Scenario: JSON output measurement
- **WHEN** the large portable fixture is emitted as canonical JSON to a regular file
- **THEN** peak RSS remains within the committed ceiling while the output validates against its declared schema

#### Scenario: Compact text output
- **WHEN** the same analysis is emitted as compact text
- **THEN** Ladon does not construct canonical JSON bytes solely to render text and still reports complete selected and omitted counts

### Requirement: Observational live scale evidence
Optional large live-repository runs SHALL record repository fingerprint,
toolchain identity, analyzer identity, scope, cache state, phase timings, peak
RSS, report sizes, and output hashes. Moving live cardinalities MUST remain
observational and MUST NOT define the portable pass/fail gate.

#### Scenario: Live repository grows
- **WHEN** an optional live repository has a different module or source-line count from an earlier run
- **THEN** Ladon records the drift with both fingerprints without changing the portable fixture's required expectations
