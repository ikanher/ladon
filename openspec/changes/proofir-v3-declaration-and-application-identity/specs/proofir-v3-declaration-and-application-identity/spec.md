## ADDED Requirements

### Requirement: Declaration identity is distinct from statement identity
ProofIR SHALL represent declaration identity as an environment-scoped qualified declaration reference distinct from the structural statement/type fingerprint used for search and comparison.

#### Scenario: Equal theorem types
- **WHEN** two qualified declarations in one environment have structurally identical types
- **THEN** they may share a statement/type fingerprint but SHALL have different declaration identities

### Requirement: Optional value identity binds its declaration
An optional value or proof fingerprint SHALL be scoped by the environment, fingerprint scheme, and exact qualified declaration name.

#### Scenario: Equal proof values under different declarations
- **WHEN** two declaration values canonicalize identically
- **THEN** their value observations do not collapse their declaration identities

### Requirement: Exact attachment requires exact declaration identity
The strongest source-attachment tier SHALL require an emitted declaration reference or an exact environment, qualified name, and declaration-identity match; a type fingerprint alone is never declaration identity.

#### Scenario: Wrong name with matching type
- **WHEN** a surface names `Pkg.Expected` but a candidate `Other.Wrong` shares its environment and type fingerprint
- **THEN** the candidate is not selected as an exact attachment

### Requirement: Residual acceptance targets the application
Checker acceptance of a candidate application with residual premises SHALL attach to a candidate-application or derivation-step subject, not to the requested goal statement.

#### Scenario: Residual premise remains
- **WHEN** Lean accepts the shape `candidate ?premise` but the premise is unproved
- **THEN** the application observation may be accepted while the goal statement result remains `unchecked`

### Requirement: Closed derivation keeps subject relationships explicit
A closed accepted derivation SHALL explicitly relate its checked application or step, conclusion statement, declaration rule, and check run without relying on equal local identifier strings.

#### Scenario: Consumer joins evidence
- **WHEN** a dossier renders the accepted closed application
- **THEN** every semantic join follows a typed reference and no claim ID is equated with an unrelated node ID

### Requirement: Candidate application identity commits to substitutions and context
A candidate-application identity SHALL commit to its environment, exact rule declaration, conclusion, ordered substitutions, ordered residual premises, local-context reference, and versioned identity scheme.

#### Scenario: One substitution changes
- **WHEN** two applications share rule, conclusion, and residuals but differ in one ordered substitution term
- **THEN** they have distinct candidate-application identities

### Requirement: Lean local context is typed evidence
Every relevant introduced or supplied local declaration SHALL be represented with a stable local ID, binder name and info, structural type, optional value, dependency order, and origin.

#### Scenario: Residual premise mentions an introduced variable
- **WHEN** applying a candidate introduces a goal binder that occurs free in a residual premise
- **THEN** the residual and application reference a context containing that binder rather than an empty-context placeholder
