## ADDED Requirements

### Requirement: One immutable execution context governs preflight and worker launch
Ladon SHALL construct one allowlisted execution environment before executable resolution or version inspection and SHALL use the same environment bytes, absolute executables, repository root, and working directory for all preflight and worker processes associated with one check.

#### Scenario: Discarded variable changes executable version output
- **WHEN** an executable reports the repository pin only while a non-allowlisted caller variable is present
- **THEN** version preflight runs without that variable and rejects the executable exactly as the worker environment would

#### Scenario: Explicit resolution fails
- **WHEN** either requested executable, repository pin, version, identity, or execution environment cannot be established
- **THEN** the operation fails closed without ambient fallback, worker launch, or an authority-bearing receipt

### Requirement: Execution fingerprints are exact and non-secret
Every attempted live check SHALL carry a canonical execution-context identity derived from the actual sanitized environment, executable identities, pin digest, repository identity, adapter identity, and selection mode, while excluding arbitrary caller variables and secret plaintext.

#### Scenario: Preflight and launch are compared
- **WHEN** a worker starts after successful preflight
- **THEN** both records reference the same execution-context identity and a mismatch is a terminal integrity failure

#### Scenario: Caller environment contains a secret
- **WHEN** a non-allowlisted secret variable is present during context construction
- **THEN** neither its name nor value appears in the context, receipt, diagnostics, artifacts, output digests, or logs produced by Ladon

### Requirement: Evidence receipt preserves independent dimensions
Ladon SHALL expose one versioned compact evidence receipt containing exact subject/environment references, execution binding, observation state, operation outcome, source freshness, environment match, authority basis, analysis completeness, and limitations without deriving one axis from another.

#### Scenario: Explicit accepted live application
- **WHEN** the explicitly pinned worker accepts one exact application under the bound context
- **THEN** the receipt records explicit-pinned execution, live observation, accepted outcome, exact environment match, elaborator-check authority, and independently derived completeness

#### Scenario: Successful observation is reloaded
- **WHEN** that result is later read from an artifact or SQLite without a new worker launch
- **THEN** observation state becomes stored while the historical execution binding and authority basis remain attributable and no fresh-live authority is claimed

#### Scenario: No check was run
- **WHEN** a search or dossier has no checker observation
- **THEN** the receipt remains absent/not-run with no execution binding and cannot acquire accepted or pinned status from surrounding fresh source evidence

### Requirement: Installed diagnostics expose posture without executing target code
`ladon doctor --json` SHALL report installed distribution identity, supported-runtime status, command/schema compatibility, repository pin availability, configured execution posture, and bounded preflight readiness without building an index or loading target Lean modules.

#### Scenario: Stale installed distribution
- **WHEN** the active console command lacks the schemas or options required by the current documentation
- **THEN** doctor reports the resolved executable and incompatible installed capability without substituting another checkout

#### Scenario: Untrusted-target posture
- **WHEN** policy requires isolation that the current platform cannot provide
- **THEN** doctor reports the unavailable posture and an authority-sensitive command configured to require it fails closed

### Requirement: Authority integrity is tested across every projection boundary
Live result, canonical artifact, SQLite row, dossier, aggregate summary, JSON renderer, and text renderer SHALL use the shared receipt/transition owner and SHALL preserve or weaken every authority-related dimension.

#### Scenario: Ambient result enters a dossier
- **WHEN** ambient-observed evidence is persisted and queried
- **THEN** no projection reports explicit-pinned execution or live observation state

#### Scenario: Invalid required child enters an aggregate
- **WHEN** one required child is invalid and the remaining children are complete
- **THEN** the aggregate reports invalid or weaker completeness and does not report a complete accepted operation

### Requirement: Execution-integrity adversarial tests run from an installed wheel
Repository-owned installed tests SHALL cover environment divergence, ambient and absent promotion attempts, live-to-stored reload, stale and mismatched evidence, failed operations, secret redaction, and cleanup after preflight or worker failure.

#### Scenario: Transition corpus is exhaustive
- **WHEN** the finite cross-product of parent axes, projection kinds, and candidate child axes is evaluated
- **THEN** every combination has one explicit accepted or rejected result and no unregistered transition is permitted
