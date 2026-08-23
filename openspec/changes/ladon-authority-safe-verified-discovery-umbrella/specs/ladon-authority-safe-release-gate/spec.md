## ADDED Requirements

### Requirement: Authority-safe release is a conjunctive integration claim
Ladon SHALL NOT advertise an `authority-safe` release state unless both proof-discovery correctness repairs and execution-authority integrity have independently passed their complete installed acceptance suites from the same candidate.

#### Scenario: Only correctness repairs pass
- **WHEN** candidate-type, naming, scope, and freshness gates pass but execution-context or transition gates fail
- **THEN** authority-safe status remains blocked

#### Scenario: Only authority repairs pass
- **WHEN** execution-context and non-escalation gates pass but discovery can still compare or scope the wrong evidence
- **THEN** authority-safe status remains blocked

### Requirement: The integration gate uses one explicit candidate
The gate SHALL materialize or build one explicit tracked candidate, install it outside the checkout, and run all required unit, adversarial, persistence, rendering, installed-CLI, quality, and OpenSpec checks against that candidate without borrowing source or dependencies from another revision.

#### Scenario: Worktree has an untracked required input
- **WHEN** a required fixture, schema, helper, or source file is absent from the explicit candidate
- **THEN** the gate fails before claiming authority-safe status

#### Scenario: Candidate passes both child suites
- **WHEN** one clean candidate passes every correctness and authority command and generated artifacts match
- **THEN** the gate emits a machine-readable receipt naming the exact candidate and each satisfied prerequisite

### Requirement: Expansion freeze is enforced until integration exit
New ProofIR families, Rust parity ownership, daemon protocols, broad service refactors, and optional product-layer expansion SHALL NOT become dependencies or release requirements while the authority-safe gate is blocked.

#### Scenario: Unrelated feature is proposed as prerequisite
- **WHEN** a new optional feature attempts to enter the dependency ledger before gate exit
- **THEN** governance validation rejects that dependency unless it is a narrowly justified correctness or security fix

### Requirement: Release documentation cannot outrun the gate
README, product scope, feature/readiness matrix, CLI documentation, maintained skills, and release evidence SHALL use the same authority-safe state and SHALL disclose blockers consistently.

#### Scenario: Gate is blocked
- **WHEN** any prerequisite remains failing or unverified
- **THEN** no maintained surface describes the release as authority-safe, semantically verified, or release-qualified
