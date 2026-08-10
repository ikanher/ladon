## ADDED Requirements

### Requirement: Worker transport is request-bound and framed
The Lean semantic worker SHALL use a versioned bounded line-framed protocol whose every frame carries an unpredictable request ID, sequence number, and exact environment identity.

#### Scenario: Target output contains a forged object
- **WHEN** process output includes brace-prefixed noise or a valid-looking object without the active request ID and sequence
- **THEN** the supervisor rejects the protocol and produces no semantic result artifact

### Requirement: Exactly one terminal frame closes the stream
The supervisor SHALL require ordered frames, exactly one terminal summary, and no trailing protocol data.

#### Scenario: Data follows the terminal frame
- **WHEN** any byte or additional frame appears after the terminal summary
- **THEN** the worker outcome is a stable protocol failure

### Requirement: Lean elaborates the request directly
The helper SHALL parse qualified names and goal syntax with Lean and elaborate the requested goal and candidate application directly in MetaM.

#### Scenario: Goal is checked
- **WHEN** a candidate is evaluated against a requested goal
- **THEN** the helper creates no generated theorem, inserts no `sorry`, and does not rely on Python source-token filtering

### Requirement: Target initializers are not executed
The semantic helper boundary SHALL not enable target-repository initializers.

#### Scenario: Repository defines a noisy initializer
- **WHEN** the target repository has an initializer that prints protocol-looking output
- **THEN** the initializer does not run and cannot affect the worker frames

### Requirement: Supervisor owns process-level check-run identity
Lean SHALL report semantic result records, while the Python supervisor SHALL construct the check-run artifact from the exact command, executable/helper identities, environment, raw output digests, resource bounds, and observed outcome.

#### Scenario: Residual result is returned
- **WHEN** Lean reports an accepted candidate shape with residual premises
- **THEN** Python can bind that result to the supervisor-observed check run without a self-referential output digest

### Requirement: Worker preserves elaboration local context
The Lean helper SHALL emit every relevant local declaration introduced or used while applying the candidate, and the supervisor SHALL validate and retain non-empty contexts.

#### Scenario: Goal binder survives application
- **WHEN** direct elaboration introduces a binder that occurs in the candidate assignment or a residual premise
- **THEN** the terminal semantic result includes its typed local declaration and the application references that context

### Requirement: Universe closure is versioned semantic policy
Any policy used to close remaining universe metavariables SHALL be explicit, versioned, represented in checker evidence, and frozen by polymorphic conformance vectors.

#### Scenario: Polymorphic equality is elaborated
- **WHEN** a goal contains equality over a universe-polymorphic type
- **THEN** the resulting structural statement is deterministic under the recorded policy and is replayed against the same Lean environment

### Requirement: Lean owns qualified-name syntax
Python SHALL restrict only transport size and control characters; Lean SHALL parse and resolve the requested module and declaration names.

#### Scenario: Unicode Lean name is requested
- **WHEN** a name is valid under the pinned Lean parser but not under Python identifier syntax
- **THEN** the request reaches Lean and is accepted or rejected by Lean's parser/resolver rather than Python syntax rules
