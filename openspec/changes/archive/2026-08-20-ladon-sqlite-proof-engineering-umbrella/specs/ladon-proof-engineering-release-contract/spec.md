## ADDED Requirements

### Requirement: Public proof-engineering contracts are synchronized
Installed help, README, CLI documentation, JSON schemas, examples, and the maintained Ladon skill SHALL describe the same ordinary CLI commands, defaults, authority fields, bounds, and security behavior.

#### Scenario: Maintained example is tested
- **WHEN** documentation and skill commands run against a freshly installed wheel
- **THEN** they parse and their text/JSON outputs satisfy the published schemas and stream contract

### Requirement: Portable semantic fixtures are authoritative
The repository SHALL include a pinned compact Lean fixture covering exact/wildcard/reducible/symmetry/coercion/instance/residual cases, structures, consumers, leakage, source-only state, malformed transport, and stale identities.

#### Scenario: No sibling checkout exists
- **WHEN** CI runs without Matrix-Factorization or Quux
- **THEN** all P0 correctness and contract gates remain executable and authoritative

### Requirement: Six plan scenarios have executable gates
The release suite SHALL cover the six implementation-plan scenarios through portable equivalents and MAY add fingerprinted real-repository calibration as observational evidence.

#### Scenario: Constructor scenario is exercised
- **WHEN** the PathBounds-equivalent fixture is queried
- **THEN** output includes field coverage, source links, residual assumptions, consumer evidence where requested, and exact omissions

### Requirement: Performance and resource claims are measured
Release evidence SHALL record cold/warm builds, cache hits, database bytes, peak RSS, SQL and Lean phase latency, p50/p95 search, constructor scaling, CLI startup, statement counts, and enforced process/output caps.

#### Scenario: Host timing varies
- **WHEN** absolute timings differ across hosts
- **THEN** release uses relative same-host regression predicates and retains raw fingerprinted measurements

### Requirement: Legacy proof-discovery overlap is reconciled
The system SHALL map every overlapping concern from `ladon-lean-proof-discovery-umbrella` to a new owner and SHALL mark it superseded only after equivalent portable exit classes pass.

#### Scenario: Legacy concern lacks replacement
- **WHEN** reconciliation finds goal-capture or frontier behavior not implemented by P0
- **THEN** that concern remains explicitly deferred or owned by its legacy packet rather than being silently closed

### Requirement: Security and proof nonclaims remain explicit
Lexical operations MUST remain no-Lean, semantic commands MUST warn that target initializers may execute and enforce process limits, and no route SHALL claim compilation without Lean verification or replay as specified.

#### Scenario: User queries an untrusted repository lexically
- **WHEN** only lexical name search is requested
- **THEN** Ladon does not load the target Lean environment
