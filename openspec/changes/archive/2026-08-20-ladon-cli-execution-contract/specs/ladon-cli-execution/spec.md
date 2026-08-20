## ADDED Requirements

### Requirement: Shared ordinary CLI
Ladon SHALL apply one public execution contract to its ordinary installed
entrypoints for interactive and automated callers.

#### Scenario: Public help
- **WHEN** a caller runs a supported public entrypoint with `--help`
- **THEN** the command exits zero and documents the same general options available to every caller of that entrypoint

#### Scenario: Supported bridge entrypoint
- **WHEN** a caller invokes `ladon-proofir-bridge`
- **THEN** it remains a general auxiliary command with the same stream, invocation-error, operational-error, and signal rules where applicable

### Requirement: No-build default
Ladon MUST NOT run Lake, Lean, or target initializers during default text
analysis, and target building SHALL require explicit `--build`.

#### Scenario: Default text run
- **WHEN** a caller runs Ladon without `--build` and with the text backend
- **THEN** no Lake or Lean subprocess is started

#### Scenario: Explicit build
- **WHEN** a caller supplies `--build`
- **THEN** Ladon records and runs the repository's documented Lake build phase before a dependent Lean phase

#### Scenario: Build with text backend
- **WHEN** a caller supplies `--build` with the text backend
- **THEN** Ladon runs a build-check phase and then text analysis without silently switching extraction backends

### Requirement: Bounded build lifecycle
Every explicit Lake build SHALL use a finite deadline and process-group
supervisor that drains output, handles cancellation, and reaps descendants.

#### Scenario: Build timeout
- **WHEN** `lake build` exceeds the default or explicit `--build-timeout`
- **THEN** Ladon terminates the process group, records timeout diagnostics, leaves no descendant, and returns operational exit code 1

#### Scenario: Build interruption
- **WHEN** the caller interrupts a running build
- **THEN** Ladon cleans up the process group and preserves the conventional signal-derived process status

### Requirement: Remove no-op skip flag
The no-op `--skip-build` option SHALL be removed, and its migration SHALL state
that omitting `--build` preserves no-build behavior. Removal MUST NOT integrate
until reconciliation's archived canonical-delta milestone passes.

#### Scenario: Legacy skip-build use
- **WHEN** a caller supplies `--skip-build` after removal
- **THEN** Ladon returns invocation exit code 2 with an actionable migration message

### Requirement: Preflight target execution
Before a requested build or Lean-backed phase, Ladon SHALL validate the
repository, root, Lake configuration, toolchain, compiled-state expectation,
and output destination relevant to that phase.

#### Scenario: Missing compiled state without build
- **WHEN** Lean-backed extraction requires unavailable compiled state and the caller did not request `--build`
- **THEN** Ladon emits an operational diagnostic that names the missing prerequisite and how to request a build

### Requirement: Single selected stdout representation
One invocation MUST write at most one report representation to stdout; report
bytes and diagnostics MUST use separate channels.

#### Scenario: Default output
- **WHEN** no format or output path is supplied
- **THEN** Ladon writes the compact text report to stdout and diagnostics only to stderr

#### Scenario: JSON stdout
- **WHEN** JSON format and `-` output are selected
- **THEN** stdout contains one valid JSON document with no progress or text-report bytes

#### Scenario: File output failure
- **WHEN** the selected report file cannot be written
- **THEN** Ladon emits the error on stderr and returns operational exit code 1

#### Scenario: Legacy dual file output
- **WHEN** both legacy `--json PATH` and `--text PATH` use regular files during the one-release compatibility period
- **THEN** both renderings are written from one report model and a deprecation warning appears only on stderr

#### Scenario: Conflicting output options
- **WHEN** legacy and canonical output flags are mixed or legacy dual output names stdout
- **THEN** Ladon returns invocation exit code 2 without starting analysis

### Requirement: General report-version selection
The analyzer SHALL expose `--report-version v2|v1`, default to v2, limit v1 to
the documented one-release compatibility period, and treat report version as a
JSON-schema selection rather than a separate analysis mode.

#### Scenario: Requested v1
- **WHEN** a caller selects `--report-version v1` with JSON as the sole representation during the compatibility period
- **THEN** the v1 adapter renders canonical v2 data and reports any information loss on stderr

#### Scenario: V1 with text
- **WHEN** a caller selects `--report-version v1` with text or legacy dual output
- **THEN** Ladon returns invocation exit code 2 before analysis and explains that v1 is a JSON-only compatibility schema

#### Scenario: Unsupported report version
- **WHEN** a caller selects an unknown or expired report version
- **THEN** Ladon returns invocation exit code 2

### Requirement: Stable process exit classes
The installed command SHALL use exit code 0 for completed requested analysis,
1 for operational failure, 2 for invocation/configuration failure, and 3 for an
explicit finding-policy rejection.

#### Scenario: Advisory findings
- **WHEN** analysis completes with findings and no `--fail-on` selector
- **THEN** Ladon returns exit code 0

#### Scenario: Invalid option
- **WHEN** command arguments or configuration are invalid
- **THEN** Ladon returns exit code 2

#### Scenario: Toolchain failure
- **WHEN** a required build, Lean extraction, timeout, input read, or report write fails
- **THEN** Ladon returns exit code 1

#### Scenario: Explicit policy match
- **WHEN** analysis completes and a documented `--fail-on` selector matches
- **THEN** Ladon returns exit code 3 and names the matching selector and findings

#### Scenario: Required phase incomplete
- **WHEN** a phase required by the invocation is partial or failed
- **THEN** Ladon returns operational exit code 1 even if a failure selector also matches

#### Scenario: Signal termination
- **WHEN** the process receives an interrupt or termination signal
- **THEN** Ladon cleans child processes and preserves the conventional signal-derived exit rather than remapping it to 1 or 3

### Requirement: Explicit finding failure policy
Findings SHALL remain advisory by default, and every configured failure
selector MUST be recorded in report metadata.

#### Scenario: Selector grammar
- **WHEN** callers repeat case-sensitive `kind:<finding-kind>`, `severity:<minimum>`, or `phase:<name>:<skipped|partial>` selectors
- **THEN** Ladon applies OR semantics, uses severity order `info < warning < error`, and records selectors plus matches in input-selector/stable-row order

#### Scenario: Invalid selector
- **WHEN** a selector has an unknown form, severity, phase status, or empty value
- **THEN** Ladon returns invocation exit code 2 before analysis

#### Scenario: Optional phase selector
- **WHEN** analysis otherwise completes and an explicit phase selector matches an optional skipped or accepted-partial phase
- **THEN** Ladon returns policy exit code 3

#### Scenario: Simultaneous policy and operational conditions
- **WHEN** a selector matches but a required phase also fails or is partial
- **THEN** operational exit code 1 takes precedence while the report retains both diagnostics

### Requirement: Input and configuration classification
The CLI SHALL distinguish invocation/configuration errors from operational
input failures and normalizable optional evidence.

#### Scenario: Invalid Ladon policy
- **WHEN** an architecture or source-pattern policy parses but violates its configuration schema
- **THEN** Ladon returns invocation exit code 2

#### Scenario: Missing or unreadable path
- **WHEN** a requested repository, root, artifact, or output path is missing or unreadable due to filesystem state
- **THEN** Ladon returns operational exit code 1

#### Scenario: Malformed optional witness
- **WHEN** an optional evidence phase can normalize a schema-invalid witness into a diagnostic
- **THEN** analysis remains advisory exit 0 unless an explicit selector rejects that diagnostic or phase state

### Requirement: Structured partial report
When trustworthy phases complete before an operational failure, Ladon SHALL
emit a report marking the failed phase before returning exit code 1.

#### Scenario: Build failure after text discovery
- **WHEN** text discovery completes and an explicitly requested build fails
- **THEN** the selected report destination contains the completed text evidence and failed build phase while the process returns 1

### Requirement: Installed entrypoint propagation
Packaged console scripts and maintained wrappers MUST propagate the canonical
CLI status unchanged.

#### Scenario: Wrapper invocation
- **WHEN** a maintained wrapper invokes a command that returns code 3
- **THEN** the wrapper process also returns code 3 without converting it to success or an operational failure
