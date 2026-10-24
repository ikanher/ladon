## Purpose

Independent source-bound prose and formal contract production with scoped coverage. This capability supports bounded prose–formal auditing with explicit evidence and limitations.

## ADDED Requirements

### Requirement: Independent prose capture
Prose contract production SHALL retain original spans and digests, attributed interpretations and alternative readings before formal matching. Elaboration or a formal match SHALL NOT establish source fidelity.

#### Scenario: Ambiguous wording matches one theorem
- **WHEN** two plausible source readings exist and only one matches selected Lean support
- **THEN** both readings and their independent fidelity status remain available

### Requirement: Supported formal extraction
Formal contract production SHALL derive supported features from elaborated environment-scoped statements or observed applications, preserving binder order, implicit arguments, local definitions and dependent domains. Authored replacements SHALL NOT be labeled extracted.

#### Scenario: Uniformity changes with binder order
- **WHEN** two declarations exchange the order of a varying parameter and an existential witness
- **THEN** the emitted contracts retain the different dependence permissions

### Requirement: Targeted extraction coverage
Production SHALL support statement-level summaries independently of complete proof extraction and SHALL request deeper slices only for explicit unresolved obligations. Coverage SHALL distinguish statement features from route and premise-provider analysis.

#### Scenario: Large proof body is unavailable
- **WHEN** a supported statement can be summarized but its proof body exceeds extraction limits
- **THEN** the statement contract remains available with provider coverage incomplete

### Requirement: Explicit unsupported features
Each unrecognized domain, scale, expression or exhausted bound SHALL produce an attributable residual. Missing feature output SHALL NOT be interpreted as absence of a mathematical requirement.

#### Scenario: Unknown dependent domain
- **WHEN** a supported outer quantifier contains a domain outside the admitted profile
- **THEN** the domain is retained as unsupported and the contract is not reported semantically complete

### Requirement: Checked presentation transport
Renaming and supported definitional presentations SHALL preserve scoped feature meaning. Nondefinitional representation transport SHALL require checked evidence and SHALL preserve restrictions and outer dependencies.

#### Scenario: Membership is erased
- **WHEN** a restricted set quantifier is mapped to an unrestricted carrier quantifier
- **THEN** the mapping is rejected or produces an unresolved transport obligation rather than an equivalent contract

### Requirement: Producer evidence replay
Produced contracts SHALL bind source bytes, environment and exact declaration/application identities so drift invalidates prior attachments. Inspection SHALL expose feature provenance and independent fidelity review.

#### Scenario: Source changed after production
- **WHEN** a quoted span or selected formal statement changes
- **THEN** the prior contract is stale and cannot be silently attached to the new source
