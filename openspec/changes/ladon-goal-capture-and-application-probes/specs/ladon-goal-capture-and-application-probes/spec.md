## Purpose

Preserve a real Lean goal and its local context while exploring theorem applications,
then explicitly replay a completed application without changing production sources.

## ADDED Requirements

### Requirement: Source-position goal capture
Ladon SHALL accept a Lean scratch file and line/column and use the pinned Lean
environment to capture the current goal and ordered local context against exact
source bytes. The capture SHALL identify source/range, selected goal, environment,
binder identities and dependencies, local values where supported, imports,
namespace/scopes and options. Unsupported or ambiguous capture SHALL fail explicitly.

#### Scenario: Active constructor field
- **WHEN** the selected position is inside an unfinished structure constructor field
- **THEN** the response includes the elaborated goal, local hypotheses, namespace/open scopes, imports, source hash, and exact position

#### Scenario: Stale position
- **WHEN** source bytes no longer match the requested capture fingerprint
- **THEN** capture fails explicitly and does not report a goal from shifted content

#### Scenario: Multiple goals share a source position
- **WHEN** a position does not identify one goal uniquely
- **THEN** the response requires explicit goal selection or reports ambiguity without silently choosing another goal

#### Scenario: A local declaration depends on earlier locals
- **WHEN** a captured goal has dependent locals or local definitions
- **THEN** their ordered identities, dependencies and available values are preserved rather than reconstructed from pretty-printed names

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
the candidate owner and spelling out the proposed application and remaining premises
during exploration. Optional exploration replay SHALL remain separate from explicit
application completion and from proof of the unfinished production declaration.

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

### Requirement: Compact applications expose contextual residuals
Ordinary application output SHALL foreground the candidate, instantiated term and
exact remaining propositions with their observed local contexts. Text and JSON
SHALL preserve evidence meaning, omissions and exact expansion references. Residual
goals SHALL NOT imply the requested goal is false or a premise is necessary for
every possible proof.

#### Scenario: Boundary-gap premise remains open
- **WHEN** an application leaves `0 ≤ Mf.DP.fixedEpochCenterGap point h boundary`
- **THEN** compact text prints that proposition and its context rather than only an unresolved metavariable name
- **AND** it identifies the application as incomplete without claiming a counterexample

#### Scenario: A residual uses newly introduced variables
- **WHEN** the residual context differs from the original goal context
- **THEN** the response preserves that observed context and does not substitute guessed or name-matched locals

### Requirement: Selected-declaration premises preserve extraction scope
The application view SHALL expose the selected declaration's authoritative
elaborated type, explicit/implicit parameters and instance requirements with exact
identity references. Authored summaries and definition expansions SHALL retain
their basis. The view SHALL NOT claim to extract all mathematically necessary
assumptions or substitute lineage frontiers for theorem premises.

#### Scenario: A definition packages an additional condition
- **WHEN** a premise summary expands that definition
- **THEN** it distinguishes the authoritative type from the expansion's source and evidence basis

### Requirement: Explicit completion requires original-goal replay
Requested application completion SHALL check the full term against the preserved
capture's original goal and context, revalidate source/environment identity, and
include independent compiler replay. Partial applications, replay not run, rejected
replay and operational failures SHALL remain distinct and SHALL NOT be reported as
completed applications. Existing exploratory acceptance labels SHALL retain their scope.

#### Scenario: A complete application is requested
- **WHEN** a caller requests completion of a term for a captured goal
- **THEN** replay is part of that operation without a separate optional switch
- **AND** the result binds that exact goal, context, term, source and environment

#### Scenario: A stored success concerns another goal
- **WHEN** supplied acceptance evidence is bound to a different goal or changed source
- **THEN** completion rejects the binding rather than inheriting that success

### Requirement: Completion reports placeholder and axiom trust
Completion SHALL report the declared trust policy and observed transitive
placeholder/axiom dependencies of the application. Default completion SHALL exclude
placeholder dependencies including `sorryAx`, distinguish allowed foundational
axioms, and disclose missing dependency coverage. Process success or a lexical
placeholder scan SHALL NOT alone establish completion under that policy.

#### Scenario: Replay compiles an application using an admitted dependency
- **WHEN** replay exits successfully but the observed application depends on `sorryAx`
- **THEN** the result reports the placeholder and does not mark default completion successful

#### Scenario: Only allowed foundational axioms are observed
- **WHEN** replay succeeds with complete dependency evidence permitted by the declared policy
- **THEN** completion reports those axioms and the policy without labeling them unfinished proofs

#### Scenario: Dependency coverage is unavailable
- **WHEN** replay succeeds but application dependency coverage cannot be established
- **THEN** the result reports the limitation without asserting unqualified completed proof status
