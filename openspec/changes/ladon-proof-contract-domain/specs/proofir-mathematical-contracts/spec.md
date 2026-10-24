## Purpose

Typed mathematical contract records, transfer rules, partial ordering and evidence identity. This capability supports bounded prose–formal auditing with explicit evidence and limitations.

## ADDED Requirements

### Requirement: Scoped contract meaning
A contract SHALL bind an exact proposition or interpretation, ordered binders, domain and scale identities, and feature-level regularity and dependence information. Unknown or unsupported features SHALL remain distinct from an empty requirement or dependency set.

#### Scenario: Unknown constant dependence
- **WHEN** a producer cannot determine a constant's permitted dependencies
- **THEN** the contract records unknown dependence and cannot be treated as a uniform constant

### Requirement: Conservative dependency claims
The contract SHALL distinguish permitted witness dependence from necessary dependence. Quantifier order and binder scope SHALL govern permitted dependencies; eliminating a parameter SHALL require checked supporting evidence.

#### Scenario: Parameter occurs in one proof
- **WHEN** a selected construction uses a parameter but another construction could avoid it
- **THEN** the record describes that construction's permission and does not assert that every witness must depend on the parameter

### Requirement: Sound partial dominance
Contract dominance SHALL compare complete correlated requirements and guarantees for the same endpoint and compatible context. Unsupported implication, scale conversion or domain transport SHALL yield unknown or incomparable rather than permit pruning.

#### Scenario: Different norm scales
- **WHEN** two estimates have identical numeric offsets but use scales with no admitted bridge
- **THEN** comparison does not declare dominance from the offsets alone

### Requirement: Admitted transfer rules
A rule used for certified propagation or pruning SHALL identify its mathematical meaning, ordered premises, side conditions, substitutions, version and checked soundness evidence. Unchecked proposed rules SHALL remain advisory.

#### Scenario: Composition requires nonnegativity
- **WHEN** a proposed scalar composition omits a required nonnegative multiplier premise
- **THEN** the rule is not admitted for that application and the missing condition remains visible

### Requirement: Closed native contract artifacts
Contract and stage-analysis records SHALL use explicitly registered closed native payloads with exact source, environment, profile and supporting references. Validators SHALL reject extra semantic fields, unresolved required references and stale identities.

#### Scenario: Mutated profile binding
- **WHEN** an analysis result is rebound to a different transfer-rule profile while retaining its prior evidence
- **THEN** validation or evidence attachment rejects the mismatch

### Requirement: Compatibility and bounded readers
Contract readers SHALL preserve existing canonical identities and native byte limits, bound all contract collections and nesting, and explicitly reject unsupported profile versions. Old readers SHALL NOT silently accept new semantics.

#### Scenario: Oversized frontier payload
- **WHEN** an otherwise valid result exceeds the native artifact byte cap
- **THEN** publication fails without replacing the destination with a truncated artifact
