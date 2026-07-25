## ADDED Requirements

### Requirement: Progress on the diagnostic channel
The ordinary installed CLI SHALL support `auto`, `plain`, `json`, and `off`
progress modes. Progress MUST use stderr only, MUST NOT contaminate report
stdout, and SHALL emit phase start, bounded update, and terminal events for
long-running discovery, extraction, analysis, and serialization.

#### Scenario: JSON report on stdout
- **WHEN** JSON report output uses stdout and progress is enabled
- **THEN** stdout remains one valid report document while stderr carries all progress events

#### Scenario: Long phase
- **WHEN** a phase remains active for more than five seconds
- **THEN** progress emits at least one bounded update every five seconds or every 100 completed modules, whichever occurs first, without emitting one event per declaration

#### Scenario: Machine-readable progress
- **WHEN** JSON progress is selected
- **THEN** each stderr line is a schema-versioned event containing run identity, phase, event kind, completed and total units when known, elapsed time, cache counters, and current status

### Requirement: Side-effect-free progress defaults
Progress auto mode SHALL enable interactive plain progress only when stderr is
an interactive terminal. Non-interactive invocations MUST remain stable and
MUST NOT gain unsolicited progress bytes.

#### Scenario: Redirected automation
- **WHEN** stderr is redirected and progress mode is `auto`
- **THEN** Ladon emits no periodic progress while final diagnostics still use stderr

#### Scenario: Explicit non-interactive progress
- **WHEN** a script selects plain or JSON progress explicitly
- **THEN** Ladon emits the requested progress format regardless of terminal detection

### Requirement: Configured overall resource limits
Ladon SHALL expose finite overall wall-time, peak-RSS, and report-byte limits
in addition to existing per-build and per-helper deadlines. Preview and report
metadata MUST record requested limits, enforcement support, observed values,
and the phase that crossed a limit.

#### Scenario: Overall wall-time exceeded
- **WHEN** total analysis reaches the configured overall deadline during an in-process or supervised phase
- **THEN** Ladon cancels remaining work, preserves validated evidence, records a timeout cause, and applies the established operational exit contract

#### Scenario: Memory limit exceeded
- **WHEN** supported runtime monitoring observes the Ladon process tree above the configured RSS limit
- **THEN** Ladon terminates supervised descendants, stops cooperative in-process work, and records the observed RSS and configured limit without claiming graceful enforcement on unsupported platforms

#### Scenario: Report-size limit exceeded
- **WHEN** bounded serialization reaches the configured report-byte limit
- **THEN** Ladon stops that representation before an oversized final file is committed and emits an actionable diagnostic naming the limit and available compact alternatives

### Requirement: Existing supervisor lifecycle
Overall timeout, cancellation, and memory-limit handling SHALL reuse the
existing process-group supervisor contract for Lake and Lean descendants.
Every terminal path MUST drain bounded diagnostics, terminate the whole group,
and reap descendants.

#### Scenario: Limit while Lean helper is active
- **WHEN** an overall limit is crossed while a Lean helper process group is running
- **THEN** the supervisor terminates and reaps that group while previously validated module frames remain available

#### Scenario: Caller interruption
- **WHEN** the caller interrupts a long run
- **THEN** Ladon performs the established descendant cleanup and preserves the conventional signal-derived process status

### Requirement: Explicit partial reasons in every report representation
Every skipped, partial, or failed phase SHALL expose a non-empty reason and
structured diagnostics through the existing report phase envelope. Compact
text MUST render the reason, failed or affected subjects, retained row counts,
and diagnostic identifiers for every required incomplete phase.

#### Scenario: Partial Lean owner run
- **WHEN** Lean extraction retains declarations but one helper or elaborated-surface operation fails
- **THEN** text and JSON both identify the concrete failure cause, successful and failed counts, affected module or batch, and retained evidence

#### Scenario: Partial discovery
- **WHEN** one source file cannot be read or parsed after other deterministic discovery units succeeded
- **THEN** the report retains successful units, marks discovery partial or failed according to required-phase policy, and names the unreadable source in a structured diagnostic

#### Scenario: No valid report model
- **WHEN** failure occurs before a schema-valid report can be constructed
- **THEN** Ladon emits a concise stderr diagnostic with identifier, cause, and exit class and does not leave a misleading report file

### Requirement: Non-empty operational stderr
Any invocation returning operational exit code 1 SHALL emit at least one
concise Ladon-authored stderr diagnostic naming the controlling cause and,
when a partial report was written, its destination. Progress history MUST NOT
be the only explanation of failure.

#### Scenario: File-backed partial report
- **WHEN** a required phase is partial and the selected report file is written
- **THEN** stderr names the phase, diagnostic identifier, reason, and report path before exit 1

#### Scenario: Multiple failures
- **WHEN** more than one phase diagnostic exists
- **THEN** stderr identifies the cause controlling exit status and points to the report for complete diagnostics without dumping unbounded helper output

### Requirement: Consistent partial acceptance policy
Partial acceptance SHALL follow the existing CLI phase-required and failure
selector contract. The report MUST record whether a partial phase was required,
accepted, rejected by strict mode, or rejected by an explicit selector, and a
strictness option MUST NOT be a semantic no-op.

#### Scenario: Accepted optional partial
- **WHEN** a non-strict optional phase returns validated rows plus diagnostics and no failure selector matches
- **THEN** Ladon retains the rows, records `partial` with accepted disposition, and returns the completed-analysis exit class

#### Scenario: Strict partial
- **WHEN** strict mode applies to a phase that returns partial data
- **THEN** the phase records strict rejection and Ladon returns operational exit code 1

#### Scenario: Required partial
- **WHEN** an invocation-required phase returns partial data
- **THEN** operational exit code 1 takes precedence while the report preserves any selector matches and retained evidence

### Requirement: Observable cache decisions
Progress, terminal diagnostics, and phase provenance SHALL reuse the existing
versioned cache status vocabulary and SHALL report hits, misses, bypasses,
invalidations, and committed writes with fingerprint version and bounded
reason codes.

#### Scenario: Warm cache hit
- **WHEN** a validated discovery or Lean extraction unit is reused
- **THEN** progress and the terminal phase envelope agree on the hit count and fingerprint version

#### Scenario: Cache bypass
- **WHEN** relevant environment or input state cannot be fingerprinted
- **THEN** Ladon reports a bypass reason and executes the unit rather than describing it as a miss followed by an unsound hit

#### Scenario: Cancellation after partial cache production
- **WHEN** cancellation occurs after some reusable units validate
- **THEN** only atomically completed units are committed and the terminal report distinguishes committed writes from discarded in-progress work

### Requirement: Deterministic partial ordering
Retained rows and diagnostics from partial runs SHALL use the same stable
ordering as complete runs and MUST NOT depend on worker completion order,
progress mode, or the moment a limit was observed beyond the recorded completed
unit boundary.

#### Scenario: Repeated controlled failure
- **WHEN** two runs use the same inputs and inject failure after the same deterministic unit
- **THEN** their normalized partial report rows, diagnostics, and completed-unit counters are identical

### Requirement: Partial-run regression gate
Required portable tests SHALL cover text discovery failure, Lean module
failure, malformed helper frames, per-helper timeout, overall timeout, memory
limit where supported, report-size limit, caller cancellation, cache
interruption, and stderr/report channel separation.

#### Scenario: Installed-candidate gate
- **WHEN** the partial-run suite exercises an installed Ladon candidate
- **THEN** every controlled failure produces the expected exit class, explicit reason, schema-valid retained report when possible, bounded cleanup, and zero orphaned descendants
