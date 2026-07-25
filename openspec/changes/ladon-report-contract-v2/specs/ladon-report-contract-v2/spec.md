## ADDED Requirements

### Requirement: Published report schema
Every v2 JSON report SHALL declare `ladon-report-v2` and validate against a
checked-in, packaged JSON Schema.

#### Scenario: Emitted report
- **WHEN** any supported analysis configuration emits JSON
- **THEN** the document validates against the schema identified in its metadata

#### Scenario: Built distribution
- **WHEN** the constrained candidate package gate inspects sdist, wheel, and isolated installation
- **THEN** `ladon:schemas/ladon-report-v2.schema.json` is present and readable from the installed package

### Requirement: Typed report boundary
Pipeline phases SHALL cross into rendering through typed, validated report
objects rather than unvalidated arbitrary top-level dictionaries.

#### Scenario: Invalid phase payload
- **WHEN** an adapter produces data that violates its typed phase contract
- **THEN** the phase is failed with a structured diagnostic instead of emitting invalid JSON

### Requirement: Explicit phase envelope
Every registered phase MUST appear with exactly one status from `complete`,
`skipped`, `partial`, or `failed`.

#### Scenario: Empty successful phase
- **WHEN** a phase runs successfully and finds zero rows
- **THEN** it is present with `complete` status and empty typed data

#### Scenario: Optional phase not requested
- **WHEN** an optional witness or packet phase is not requested
- **THEN** it is present with `skipped` status and a human-readable reason

#### Scenario: Partial extraction
- **WHEN** a phase returns validated rows plus module-level failures
- **THEN** it is present with `partial` status, the rows, and structured diagnostics

### Requirement: Preserved textual reasons
Skip, partial, and failure reasons SHALL be preserved as text and MUST NOT be
replaced by a length or opaque counter.

#### Scenario: Text backend skips Lean
- **WHEN** the text backend skips Lean extraction because it was not selected
- **THEN** the report contains that textual reason verbatim as structured Ladon-authored data

### Requirement: Deterministic normalized serialization
Equivalent repository state, arguments, toolchain, and explicit metadata SHALL
produce byte-identical normalized JSON with documented stable collection order.

#### Scenario: No explicit timestamp
- **WHEN** two equivalent runs omit a generated timestamp
- **THEN** normalized report bytes are identical and no wall-clock timestamp is injected

#### Scenario: Explicit timestamp
- **WHEN** the caller supplies a timestamp
- **THEN** it is preserved in the volatile metadata field without changing analysis selection

### Requirement: Text and JSON semantic parity
Text rendering SHALL consume the same report objects as JSON and SHALL preserve
full selected counts, phase states, and the fields of every row it renders.

#### Scenario: Finding parity
- **WHEN** compact text summarizes a report with more detailed JSON rows than it displays
- **THEN** text reports the complete selected totals and omitted-row counts, and each displayed row uses the same identifier, evidence count, severity, and authority as JSON

### Requirement: Versioned extension namespaces
The report contract SHALL provide registered, versioned extension envelopes and
MUST NOT grow arbitrary top-level keys.

#### Scenario: Absent extension
- **WHEN** an optional extension is not available
- **THEN** its registered phase or extension state remains explicit without invalidating the base report

#### Scenario: Authority-bearing extension
- **WHEN** an extension includes external or Lean-backed evidence
- **THEN** the concrete capability owner supplies its payload schema while the generic envelope requires version, authority, and provenance hooks

### Requirement: Compatibility transition
The implementation SHALL provide fixed v1 compatibility fixtures and a
documented transition path; it MUST NOT mutate `clean-core-1` semantics in
place.

#### Scenario: Requested v1 serialization
- **WHEN** the caller uses the shared CLI's general `--report-version v1` with JSON as the sole representation during the one-release compatibility period
- **THEN** canonical v2 data is converted where representable and information-loss warnings are emitted

#### Scenario: Requested v1 text
- **WHEN** the caller combines `--report-version v1` with text or legacy dual output
- **THEN** the CLI rejects the invocation before analysis because v1 is a JSON compatibility serializer

### Requirement: Reader version checks
Atlas, SQLite, diff, and workflow readers MUST reject unsupported report
versions clearly and MUST accept schema-valid v2 reports.

#### Scenario: Unknown major version
- **WHEN** a reader receives a report with an unknown major contract
- **THEN** it returns an actionable unsupported-version diagnostic rather than guessing field semantics
