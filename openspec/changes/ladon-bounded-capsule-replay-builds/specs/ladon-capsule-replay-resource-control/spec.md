# Capsule replay resource control

## Purpose

Allow callers to select an enforceable bounded-build policy for isolated theorem capsule replay and receive actionable resource evidence without weakening the existing verification contract.

## ADDED Requirements

### Requirement: Explicit enforceable build policy
Replay SHALL expose an explicit bounded-build policy through its public service and CLI. It MUST enforce the promised limit on the selected expensive build work, or reject an unsupported policy before expensive target execution. An ignored flag or unverified caller environment variable MUST NOT be reported as an enforced limit.

#### Scenario: Restricted policy is supported
- **WHEN** a caller selects a valid restricted build policy
- **THEN** execution enforces that policy and the receipt identifies the requested and effective policy

#### Scenario: Policy is unavailable
- **WHEN** the pinned toolchain or replay strategy cannot enforce the requested policy
- **THEN** replay emits a clear unsupported or invalid-invocation outcome rather than running unrestricted while claiming enforcement

### Requirement: Verification semantics survive scheduling changes
A resource-controlled replay MUST retain capsule-content validation, fresh-root isolation, pinned toolchain and locked dependencies, exact theorem/dependency identity comparison and trust-frontier checks. It MUST NOT use project OLeans or undeclared paths from the original checkout to reduce build cost.

#### Scenario: Original checkout is unavailable
- **WHEN** a restricted-policy replay runs after the source checkout has been renamed or made unavailable
- **THEN** it verifies or fails from the declared capsule inputs without resolving project artifacts from the original path

#### Scenario: Build completes but comparison differs
- **WHEN** the restricted build succeeds but theorem, dependency or trust evidence differs
- **THEN** replay reports the existing mismatch outcome and MUST NOT return verified

### Requirement: Finite supervised attempt
Restricted execution SHALL preserve finite timeout, process-tree RSS, output and cancellation controls. If building is split into subprocesses, timeout accounting MUST explicitly bound the attempt and MUST NOT silently reset an unlimited deadline for each module. Resource limits MUST NOT be raised or disabled automatically.

#### Scenario: Compiler descendants exceed RSS
- **WHEN** the controlled build or its descendants exceed the configured RSS ceiling
- **THEN** the whole supervised process group is terminated and the receipt identifies memory exhaustion and the failing stage

#### Scenario: Controlled build times out or is cancelled
- **WHEN** a deadline or cancellation occurs
- **THEN** replay cleans up descendants, records the bounded outcome and does not continue to verification

### Requirement: Actionable resource receipt
Replay SHALL report the selected build policy, resource limits, failing stage and bounded evidence sufficient to distinguish aggregate fan-out from a single expensive child where measured. Peak process-tree RSS MUST remain labelled as an aggregate metric; another memory metric MUST NOT silently replace its meaning.

#### Scenario: Large aggregate build fails
- **WHEN** the459-module integration capsule exceeds its configured cap
- **THEN** the receipt retains the cap and sampled peak and reports available policy/fan-out/child-stage evidence without inferring mathematical rejection

#### Scenario: Child details are unavailable
- **WHEN** the implementation cannot obtain a requested measurement
- **THEN** it explicitly marks that measurement unavailable rather than inventing a causal explanation

### Requirement: Small-fixture gate before expensive replay
The change SHALL include deterministic tests of policy enforcement, invalid-policy handling, descendant cleanup and receipt classification, plus a small pinned-toolchain integration fixture. The real large-capsule case SHALL remain a separate integration reproducer with an explicit resource budget.

#### Scenario: Regression suite runs
- **WHEN** ordinary policy tests run
- **THEN** they validate enforcement and failure handling without requiring the full research checkout or a48GiB allocation

#### Scenario: Large-capsule integration is attempted
- **WHEN** the real reproducer is run after the small fixture passes
- **THEN** its exact inputs, budget and achieved build/comparison status are recorded separately; failure does not invalidate a mathematical theorem or count as verification
