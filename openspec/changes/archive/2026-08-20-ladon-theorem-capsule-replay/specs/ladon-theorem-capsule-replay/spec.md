## ADDED Requirements

### Requirement: Content validation precedes execution
Replay MUST validate capsule schema, plan identity, normalized paths, complete file
inventory, hashes, modes, toolchain/lock metadata, and guarantee compatibility
before invoking Lean, Lake, or any target-controlled process.

#### Scenario: Capsule file was mutated
- **WHEN** any inventoried file, manifest field, or plan identity differs from the materialized evidence
- **THEN** replay returns content-invalid and starts no target toolchain process

#### Scenario: Undeclared file can affect resolution
- **WHEN** the capsule contains an unaccounted source, configuration, plugin, or package-resolution input
- **THEN** replay fails closed instead of allowing that file to influence verification

### Requirement: Replay is independent of the original checkout
Replay SHALL operate from a fresh root in which the original repository is
unavailable. The original path MUST be absent from the working directory, Lean
path, Lake environment, generated configuration, command arguments, and allowed
repository input roots.

#### Scenario: Capsule accidentally depends on original source
- **WHEN** a required module or resource exists only in the original checkout
- **THEN** clean-room replay fails and MUST NOT resolve that input from the original path

#### Scenario: Original checkout is renamed or unreadable
- **WHEN** a complete capsule is replayed while the source checkout cannot be accessed
- **THEN** the result is unchanged by the checkout's absence

### Requirement: Pinned and supervised Lean execution
Replay MUST use the capsule's compatible pinned Lean toolchain and locked package
metadata. Every invoked process and descendant SHALL run under Ladon's established
time, memory, process-tree, and output limits, with dependency availability
distinguished from Lean rejection.

#### Scenario: Lean accepts the capsule
- **WHEN** locked dependencies are available and the pinned toolchain successfully compiles the target source
- **THEN** replay advances to exact theorem and evidence comparison

#### Scenario: Resource limit is exceeded
- **WHEN** Lean, Lake, a helper, or a descendant exceeds a configured supervision limit
- **THEN** replay terminates the process tree and reports a resource-limit status

#### Scenario: Locked package cannot be acquired
- **WHEN** an external dependency is absent and permitted acquisition cannot obtain the locked revision
- **THEN** replay reports dependency-unavailable rather than Lean-rejected or verified

### Requirement: Exact theorem and structural evidence comparison
After successful compilation, the pinned Lean environment MUST confirm the exact
fully qualified theorem and compare declaration kind, a versioned
toolchain-scoped type fingerprint, value fingerprint when supported, semantic
dependency evidence, and trust frontier with the plan. Pretty-printed theorem text
MUST NOT be the sole identity authority.

#### Scenario: Same name resolves to changed theorem
- **WHEN** the capsule compiles but the exact theorem's structural fingerprint or declaration kind differs from the plan
- **THEN** replay reports identity-mismatch and does not mark the capsule verified

#### Scenario: Value fingerprint is unsupported
- **WHEN** the pinned Lean/helper version cannot produce the value fingerprint required by the plan's comparison level
- **THEN** replay reports an incompatible or unsupported facet instead of silently skipping the comparison

#### Scenario: Trust frontier changes
- **WHEN** replayed dependencies or trust facts differ from the planned closure
- **THEN** replay reports an evidence mismatch with typed differences

### Requirement: Structured replay receipt and bounded claims
Replay SHALL emit a canonical machine-readable receipt containing capsule, plan,
toolchain, and helper identities; achieved isolation facts; ordered stages;
sanitized commands; bounded output evidence; exit classifications; dependency
acquisition facts; theorem comparisons; trust frontier; and final status. A
verified status MUST mean only that the recorded Lean replay contract succeeded.

#### Scenario: Replay succeeds
- **WHEN** content, isolation, toolchain execution, theorem identity, dependency, and trust checks all succeed
- **THEN** the receipt records verified and retains nonclaims about Ladon proof authority, global minimality, offline vendoring, and system hermeticity

#### Scenario: Receipt includes sensitive host data
- **WHEN** commands or environments contain host paths, credentials, or tokens outside the evidence contract
- **THEN** the receipt redacts them while retaining stable role-based diagnostics and hashes

### Requirement: Actionable replay failure taxonomy
Replay MUST distinguish at least content-invalid, environment-unavailable,
dependency-unavailable, unsupported-facet, resource-limit, Lean-rejected,
identity-mismatch, isolation-violation, and verified outcomes. Failure receipts
MUST identify the stage and bounded cause without publishing partial success as
verification.

#### Scenario: Lean rejects the proof source
- **WHEN** the pinned Lean compiler reports an error after successful content and environment setup
- **THEN** replay classifies the result as Lean-rejected with bounded compiler evidence

#### Scenario: Original path leaks into resolution
- **WHEN** an isolation check observes the original checkout in a command, environment, resolved input, or allowed root
- **THEN** replay stops with isolation-violation even if Lean would otherwise succeed

### Requirement: Caller-neutral replay and composed extraction CLI
The installed CLI SHALL expose an ordinary replay operation for an existing
capsule and an extract-with-verification flow that composes the same planning,
materialization, and replay services. Both MUST follow the existing clean
stdout/stderr and exit-status contract and MUST support canonical JSON output.

#### Scenario: User replays an existing capsule
- **WHEN** a user invokes the installed replay command on a valid capsule
- **THEN** Ladon runs the clean-room checks and returns the receipt identity and final status

#### Scenario: User extracts with verification
- **WHEN** a user requests theorem extraction with verification
- **THEN** Ladon executes the three phase contracts in order and reports verified only after the replay phase succeeds

#### Scenario: JSON output is requested
- **WHEN** a caller selects canonical JSON representation
- **THEN** stdout contains one machine-readable result while progress and bounded diagnostics follow the established diagnostic channel
