## ADDED Requirements

### Requirement: One immutable execution context governs preflight and worker launch
Ladon SHALL capture immutable allowlisted inputs before resolving absolute executables and existing compiled-library roots. It SHALL then freeze the final environment before version inspection or source enumeration. All preflight and worker processes for a check SHALL use identical environment bytes, repository root, and working directory. Auxiliary Git SHALL retain its absolute executable identity from those inputs and use the same final environment.

#### Scenario: Discarded variable changes executable version output
- **WHEN** an executable reports the repository pin only while a non-allowlisted caller variable is present
- **THEN** version preflight runs without that variable and rejects the executable exactly as the worker environment would

#### Scenario: Explicit resolution fails
- **WHEN** either requested executable, repository pin, version, identity, or execution environment cannot be established
- **THEN** the operation fails closed without ambient fallback, worker launch, or an authority-bearing receipt

#### Scenario: An explicitly empty environment is supplied
- **WHEN** a caller supplies an empty environment mapping instead of omitting the environment argument
- **THEN** context construction does not inherit host variables or resolve ambient executables through the host search path
- **AND** explicit executable selection can construct its own bounded PATH without adding other host values

#### Scenario: A caller constructs a context with unsupported variables
- **WHEN** a directly constructed toolchain context contains a key outside the supported base allowlist and validated derived-library-path field
- **THEN** construction fails before preflight or worker use and the diagnostic does not echo the unsupported key or value

#### Scenario: Compiled-library search paths change after base context creation
- **WHEN** direct-Lean preparation derives a different library-path environment from the one bound to the final execution context
- **THEN** execution fails closed or constructs and validates a new final context before launch rather than reusing the old identity for changed environment bytes
- **AND** auxiliary source-enumeration processes retain explicit environment provenance instead of silently inheriting a different caller environment

#### Scenario: Worker repository differs from the recorded context
- **WHEN** direct-Lean preparation receives a repository root different from the bound context
- **THEN** it rejects the request before launching a process

#### Scenario: Host environment or Git changes after selection
- **WHEN** host variables change after context construction
- **THEN** source verification retains the selected Git and exact captured process environment
- **AND** changed or missing selected Git bytes fail closed instead of selecting another executable

### Requirement: Execution fingerprints are exact and non-secret
Every attempted live check SHALL carry a canonical execution-context identity derived from the actual sanitized environment, executable identities, pin digest, repository identity, adapter identity, and selection mode, while excluding arbitrary caller variables and secret plaintext.

#### Scenario: Preflight and launch are compared
- **WHEN** a worker starts after successful preflight
- **THEN** both records reference the same execution-context identity and a mismatch is a terminal integrity failure

#### Scenario: Caller environment contains a secret
- **WHEN** a non-allowlisted secret variable is present during context construction
- **THEN** its value and any opaque caller key name are absent from the context, receipt, diagnostics, artifacts and logs produced by Ladon, and do not influence context or output identities
- **AND** a known key such as `LEAN_PATH` may be recorded only for Ladon-derived data, never for its discarded caller value

#### Scenario: Maintained discarded-input regression gate
- **WHEN** the execution nonleakage gate runs against an installed candidate
- **THEN** it exercises direct accepted/rejected/residual results, batch/discovery and scratch, ambient execution, preflight/worker failures and bounded termination
- **AND** it checks captured child environments, diagnostics, progress, canonical artifacts, receipts, JSON/text renderers, stored expansion and SQLite/WAL bytes for synthetic discarded inputs
- **AND** required mode fails instead of skipping when the pinned Lean fixture toolchain is unavailable
- **AND** finite fixture coverage is not presented as target-code isolation or protection of secrets supplied through allowed paths, sources or goals

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

#### Scenario: Required isolation is unavailable before preflight
- **WHEN** a caller supplies `--require-isolation` to candidate checking or discovery under the trusted-repository profile
- **THEN** the command returns the operational diagnostic `target-isolation-unavailable` before executable preflight, target loading, index access, output-file creation, or evidence publication
- **AND** `doctor --json --require-isolation` reports the same policy availability while keeping target execution and preflight not-run

### Requirement: Authority integrity is tested across every projection boundary
Live result, canonical artifact, SQLite row, dossier, aggregate summary, JSON renderer, and text renderer SHALL use the shared receipt/transition owner and SHALL preserve or weaken every authority-related dimension.

#### Scenario: Ambient result enters a dossier
- **WHEN** ambient-observed evidence is persisted and queried
- **THEN** no projection reports explicit-pinned execution or live observation state

#### Scenario: Canonical check evidence is expanded from storage
- **WHEN** a stored canonical check artifact includes a valid, owner-bound evidence receipt
- **THEN** expansion returns a current-read receipt with stored observation state and preserved historical binding, outcome, authority, freshness, and completeness
- **AND** the canonical artifact bytes remain unchanged; an invalid receipt identity or mismatched check/environment owner rejects the read

#### Scenario: Invalid required child enters an aggregate
- **WHEN** one required child is invalid and the remaining children are complete
- **THEN** the aggregate reports invalid or weaker completeness and does not report a complete accepted operation


#### Scenario: Native check records enter a theorem dossier
- **WHEN** an exact visible theorem subject owns a native check run with a valid canonical receipt
- **THEN** the bounded `checks` section exposes that check's receipt with stored observation state and unchanged historical dimensions
- **AND** the dossier query receipt remains not-run; missing receipts do not acquire inferred execution authority

#### Scenario: A fresh dependency closure is read and aggregated
- **WHEN** a lineage query, graph, or summary reads a stored exact closure without an application check receipt
- **THEN** the query receipt has no execution binding, no check/environment references, not-run outcome, and not-assessed environment match and checking completeness
- **AND** graph and summary projections use derived observation state while missing closures remain absent
- **AND** opaque closure IDs retain typed lineage references without digest or kernel-authority claims

#### Scenario: Discovery receipts enter a compact aggregate
- **WHEN** a partial discovery population includes a candidate check and a separate scratch observation
- **THEN** each available receipt is projected separately as derived with unchanged historical dimensions and exact source/derived receipt identities
- **AND** missing child receipts remain missing, omitted candidates remain counted, and byte fitting does not remove authority dimensions from visible scratch cards
- **AND** JSON and text expose the same dimensions without synthesizing aggregate checker acceptance

#### Scenario: A stored structural derivation is inspected
- **WHEN** the ordinary CLI reads route, slice, or alternatives evidence from an exact content-owned derivation artifact
- **THEN** the reader receipt binds the operation, typed query inputs, owner, and bounds while reporting no execution binding, not-run checking, and not-assessed environment matching and checking completeness
- **AND** complete structural analysis does not promote these axes, invalid targets have failed observations, and content/lookup owner mismatches are rejected before traversal

#### Scenario: A rehashed stored receipt contradicts its canonical check
- **WHEN** a receipt has valid content identity and matching check/environment references but contradicts canonical candidate, module, goal, application context, outcome, or completeness
- **THEN** stored expansion and theorem dossiers reject it through the shared semantic observation owner before rendering an authority claim
- **AND** result subjects must be exact typed declared inputs, contradictory terminal children are rejected, and unsupported receipt operations fail closed
- **AND** scratch caller-context prefixes and provisional process observations retain the existing owner semantics; absent canonical context evidence is not invented

#### Scenario: A rejected receipt contradicts its recorded local context
- **WHEN** an exact candidate check is rejected after the worker has observed its ordered local context
- **THEN** its CheckRun owns a typed local-context subject and declares that subject as an input
- **AND** live projection, stored expansion, and theorem dossier readers reject receipts whose normalized context differs in names, types, order, or length from that input, even if the receipt identity is recomputed
- **AND** ambiguous, undeclared, unowned, or malformed recorded context inputs fail closed
- **AND** older rejected checks without a recorded context input remain readable without inferred independent context correspondence

#### Scenario: A historical receipt changes its recorded execution binding
- **WHEN** a receipt has been correctly rehashed but its execution selection or CheckRun executable identity contradicts the exact input-owned environment's recorded selection/worker evidence
- **THEN** live semantic projection and stored artifact/dossier reads reject that contradiction
- **AND** recorded context JSON with duplicate keys, unsupported selection mode, invalid required content identities, or inconsistent pin content is rejected rather than treated as absent
- **AND** lookup uses exact declared environment artifact inputs, not a name, current host paths, or a newly executed checker

#### Scenario: Ambient selection uses a launcher
- **WHEN** an ambient toolchain context selects an elan launcher and the worker reports a distinct Lean executable
- **THEN** the environment records the observed worker executable digest separately from the selected executable identity
- **AND** readers validate the CheckRun executable against the recorded worker digest without claiming explicit-pinned selection
- **AND** explicit selection additionally requires equality between the selected Lean identity and the CheckRun worker identity
- **AND** an older ambient context without recorded worker identity weakens stored binding to `none` when the launcher/worker relation is unknown

#### Scenario: Process evidence records selected execution context
- **WHEN** scratch compilation or an interrupted batch produces a partial process receipt
- **THEN** its CheckRun executable identity is checked against the recorded selected toolchain identity
- **AND** the environment's elaborator-worker identity is not treated as a new worker observation for that process operation
- **AND** ambient selection remains ambient, process authority remains partial, and a mismatched selected executable is rejected

#### Scenario: Historical execution metadata is absent
- **WHEN** a stored check has a valid receipt but no independently available input environment or recorded toolchain context
- **THEN** its returned read receipt weakens execution binding to `none` and adds an explicit limitation through the shared transition owner
- **AND** its canonical artifact and original receipt remain unchanged, its other evidence axes retain their reported meaning, and subsequent projections cannot recover stronger binding
- **AND** bounded dossier lookup preserves exact content ownership without adding per-row environment queries

#### Scenario: Compact historical binding cannot bypass the read boundary
- **WHEN** a compact candidate or scratch observation resolves to canonical evidence without independent recorded toolchain context, or to an older ambient launcher record with unknown worker relation
- **THEN** its projected receipt weakens execution binding to `none` through the same owner as stored reads
- **AND** an unbound direct observation first becomes stored, while a discovery aggregate becomes derived; accepted, rejected, failed, and provisional outcomes retain their reported scope and independent dimensions
- **AND** JSON, text, and minimal cards preserve the finite weakening reason and exact source/projected receipt identities without modifying canonical input bytes or starting Lean
- **AND** independently bound explicit and ambient records preserve their binding; malformed or contradictory evidence anywhere in the population is rejected before display selection
- **AND** the raw audit projection remains a detached canonical-source copy rather than a new read receipt, and weak failures without canonical checks retain their existing scope

#### Scenario: A weak observation contains a malformed receipt
- **WHEN** a failed or unassessed candidate, or an unattributed scratch failure, supplies a non-null receipt that is not an object
- **THEN** compact population validation rejects it before display selection, including when the affected row would be omitted
- **AND** genuinely absent or null receipts remain supported without inheriting authority completeness from public fields

#### Scenario: Weak and raw-source boundaries remain visible
- **WHEN** a weak failure without canonical checks has a valid receipt
- **THEN** compact output retains its attempted toolchain selection, failed outcome, and non-checker scope without inventing environment/check references
- **AND** raw audit JSON remains an unchanged detached copy without registry writes; raw audit text identifies its original observations and unrevalidated execution binding
- **AND** stored text receipts expose the finite historical binding limitation when present

### Requirement: Execution-integrity adversarial tests run from an installed wheel
Repository-owned installed tests SHALL cover environment divergence, ambient and absent promotion attempts, live-to-stored reload, stale and mismatched evidence, failed operations, secret redaction, and cleanup after preflight or worker failure.

#### Scenario: Transition corpus is exhaustive
- **WHEN** the finite cross-product of parent axes, projection kinds, and candidate child axes is evaluated
- **THEN** every combination has one explicit accepted or rejected result and no unregistered transition is permitted

#### Scenario: Receipt projections compose without restoring authority
- **WHEN** a valid receipt passes through successive registered persistence, aggregate, canonical, or renderer boundaries
- **THEN** equivalent routes preserve the same receipt identity and every independent dimension except the permitted observation-state weakening
- **AND** stale/mismatched inputs, failed or absent observations, partial/invalid scope, exact subject references, and limitations retain their meaning
- **AND** once historical execution binding has weakened to none, no later boundary may restore ambient or explicit binding
