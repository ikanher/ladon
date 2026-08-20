## ADDED Requirements

### Requirement: Versioned generic analysis runset
Ladon SHALL accept a versioned runset manifest that names ordinary analysis
entries, their repository-relative roots and scopes, documented public CLI
options, output identities, and required or advisory status. The manifest MUST
remain repository-generic and MUST NOT contain caller-specific behavior or
built-in Matrix-Factorization, Quux, or mathlib paths.

#### Scenario: Valid runset manifest
- **WHEN** a caller supplies a supported runset manifest containing several roots
- **THEN** Ladon validates the complete manifest before execution and records its schema version and normalized fingerprint

#### Scenario: Unsupported runset version
- **WHEN** a caller supplies an unknown runset major version
- **THEN** Ladon returns the shared invocation-error exit class before starting any target process

#### Scenario: Non-portable required entry
- **WHEN** a required portable manifest embeds an absolute maintainer path or hidden sibling-repository dependency
- **THEN** the portable gate rejects the manifest before analysis

### Requirement: One canonical report per root
Each runset entry SHALL execute the same ordinary one-root Ladon analysis
contract and SHALL produce one independently schema-valid canonical report for
that root. A runset MUST NOT merge several roots into a new analyzer report or
apply alternate thresholds, findings, or evidence authority.

#### Scenario: Multi-root plan
- **WHEN** a runset contains three valid root entries
- **THEN** successful execution produces three separately addressable canonical reports and one bundle manifest that references them

#### Scenario: Shared root with distinct scope
- **WHEN** two entries intentionally analyze the same root with distinct documented scopes or backends
- **THEN** each entry receives a distinct stable run identity and report without overwriting or blending the other entry

### Requirement: Serial and bounded execution lifecycle
Runsets MUST execute entries serially by default and SHALL reuse the existing
finite process supervisor for every requested build or Lean extraction.
Any explicit concurrency mode MUST have a finite documented bound and MUST
preserve cancellation, output draining, escalation, and descendant cleanup.

#### Scenario: Default execution
- **WHEN** a caller runs a multi-entry manifest without a concurrency option
- **THEN** no two target build or Lean helper process groups execute concurrently

#### Scenario: Runset cancellation
- **WHEN** the caller interrupts a runset while an entry owns a target process group
- **THEN** Ladon terminates and reaps that group, records the interrupted entry, preserves completed reports, and starts no later entry

### Requirement: Shared fingerprinted reuse
Runsets SHALL share immutable discovery indexes, content hashes, and compatible
Lean caches across entries when their full validity fingerprints agree.
Reuse MUST be recorded per entry and MUST NOT allow one root's partial or
incompatible state to contaminate another root's report.

#### Scenario: Compatible shared inventory
- **WHEN** several roots use the same unchanged repository inventory and compatible extraction options
- **THEN** Ladon reuses the validated index or cache and records the reused fingerprint in each affected entry

#### Scenario: Incompatible extraction state
- **WHEN** a root, source closure, toolchain, helper, Lake configuration, or extraction option changes
- **THEN** only entries whose validity fingerprints are affected are invalidated and rerun

### Requirement: Durable resumable runset state
Ladon SHALL write durable runset state atomically after each terminal entry
state and SHALL resume only reports whose entry fingerprint, report version,
content hash, and completion state remain valid. Interrupted, malformed,
partial-required, or manually changed output MUST NOT be treated as a valid
completed entry.

#### Scenario: Unchanged resume
- **WHEN** a completed runset is resumed with identical inputs and intact reports
- **THEN** Ladon performs zero analyzer or target-process launches and records every entry as a validated resume hit

#### Scenario: One entry changed
- **WHEN** one entry or one input in its resolved validity closure changes before resume
- **THEN** Ladon reruns that affected entry while preserving valid unaffected reports

#### Scenario: Crash during report publication
- **WHEN** execution stops before an entry report and its terminal state are atomically committed
- **THEN** the next resume treats that entry as incomplete and never accepts a truncated report as valid

### Requirement: Per-entry failure isolation
A runset SHALL preserve every completed report and diagnostic when another
entry fails. The bundle manifest MUST record complete, skipped, partial,
failed, interrupted, and resume-hit states separately, and aggregate process
status SHALL follow the shared CLI precedence for required and advisory work.

#### Scenario: Required entry fails
- **WHEN** one required entry fails after earlier entries completed
- **THEN** earlier reports remain valid, the failed entry retains structured diagnostics or a partial report when possible, later-entry handling follows the declared stop policy, and the runset returns the operational-failure exit class

#### Scenario: Advisory entry fails
- **WHEN** an advisory entry fails and the manifest permits continuation
- **THEN** Ladon records that failure, continues with later entries, and does not relabel the failed entry as skipped or complete

### Requirement: Deterministic portable bundle manifest
Every runset SHALL emit a deterministic versioned bundle manifest with stable
entry order, repository-relative report paths, root and scope identity, report
version and content hash, input fingerprint, reuse state, phase status summary,
and bounded resource counters. Host-specific absolute paths and volatile
timings MUST be isolated from normalized deterministic comparison.

#### Scenario: Equivalent runsets
- **WHEN** equivalent runsets execute with equal explicit metadata and normalized resource fields
- **THEN** their normalized bundle manifests are byte-identical

#### Scenario: Bundle moved as a directory
- **WHEN** a completed bundle is moved without changing its internal relative layout
- **THEN** every report reference still resolves and validates

### Requirement: Runset stream discipline and progress
Runset report or manifest output SHALL obey the shared CLI stream contract.
Structured progress and per-entry lifecycle events MAY be emitted only on
stderr or an explicitly selected progress destination and MUST NOT corrupt
machine-readable stdout.

#### Scenario: JSON bundle on stdout
- **WHEN** a caller selects the bundle manifest as JSON stdout output
- **THEN** stdout contains exactly one valid bundle document while entry progress and diagnostics appear only on stderr

#### Scenario: Quiet resumed run
- **WHEN** a caller disables progress for an unchanged resumed run
- **THEN** the selected report output remains complete and no hidden diagnostic or progress bytes are added to stdout

### Requirement: Portable runset acceptance
Required runset gates SHALL execute an installed clean-candidate CLI against a
tracked generated multi-root fixture. The gates MUST cover deterministic
bundles, serial default execution, compatible reuse, selective invalidation,
failure isolation, cancellation cleanup, and resume without depending on a
live sibling repository.

#### Scenario: Required generated fixture
- **WHEN** the portable runset gate executes its positive, failure, interruption, and resume cases
- **THEN** report counts and states match the manifest, all reports validate, no helper descendant remains, and normalized bundle output is deterministic

#### Scenario: Optional live repository evidence
- **WHEN** Matrix-Factorization or another explicitly configured live repository is available
- **THEN** Ladon records its revision, toolchain, environment, timings, RSS, helper counts, and output hashes as observational evidence without turning moving counts into portable correctness assertions
