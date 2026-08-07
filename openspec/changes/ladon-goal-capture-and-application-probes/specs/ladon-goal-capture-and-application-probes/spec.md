## ADDED Requirements

### Requirement: Source-position goal capture
Ladon SHALL accept a Lean scratch file and line/column and use the pinned Lean
environment to capture the current goal and local context against exact source bytes.

#### Scenario: Active constructor field
- **WHEN** the selected position is inside an unfinished structure constructor field
- **THEN** the response includes the elaborated goal, local hypotheses, namespace/open scopes, imports, source hash, and exact position

#### Scenario: Stale position
- **WHEN** source bytes no longer match the requested capture fingerprint
- **THEN** capture fails explicitly and does not report a goal from shifted content

### Requirement: Local hypothesis to binder mapping
Captured hypotheses SHALL be compared with candidate binders through Lean-backed
matching and reported individually.

#### Scenario: Partial local discharge
- **WHEN** local hypotheses satisfy some but not all candidate premises
- **THEN** the route shows each satisfied binder and forwards only the residual premises to difference analysis

### Requirement: Compiler-error query normalization
Ladon SHALL accept relevant Lean type-mismatch diagnostics as query input while
distinguishing parsed text from re-elaborated goal evidence.

#### Scenario: Unresolved field error
- **WHEN** a caller provides a constructor type mismatch and its source location
- **THEN** Ladon attempts source-position capture and labels any unconfirmed parsed fragments as caller-supplied evidence

### Requirement: Isolated minimal application probe
Ladon SHALL emit and optionally compile a separate minimal scratch `example` importing
the candidate owner and spelling out the proposed application and remaining premises.

#### Scenario: Successful probe
- **WHEN** the generated example compiles under the pinned toolchain
- **THEN** the route card records Lean-confirmed probe success, exact imports, source content hash, and toolchain/helper identity

#### Scenario: Failed probe
- **WHEN** Lean rejects the generated example
- **THEN** the route remains rejected or conditional with bounded compiler diagnostics and no production source change

### Requirement: Scratch isolation and supervision
Goal capture and probes MUST use temporary artifacts outside production source and
finite supervised Lean processes.

#### Scenario: Probe completion
- **WHEN** a probe succeeds, fails, times out, or is interrupted
- **THEN** Ladon reaps the process tree, retains classified evidence, and leaves the target repository unchanged
