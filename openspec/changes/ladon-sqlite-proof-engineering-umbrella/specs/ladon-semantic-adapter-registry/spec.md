## ADDED Requirements

### Requirement: Adapter registries are versioned and inspectable
The system SHALL load a versioned built-in registry and optional validated repository JSON rules with rule ID, source, direction, declaration, cost, side-condition template, fingerprint, and precedence.

#### Scenario: Repository defines a representation transport
- **WHEN** the policy validates and its named declaration resolves
- **THEN** the rule is available with repository-policy authority and exact provenance

### Requirement: Policy never becomes theorem authority
A registry rule MUST remain advisory until Lean verifies the named adapter application in the current module environment; every side condition SHALL become a residual goal.

#### Scenario: Named adapter does not apply
- **WHEN** the policy names an existing theorem whose direction or types do not match
- **THEN** the route is rejected with Lean evidence and is not promoted because policy selected it

### Requirement: Registry failures are explicit
Absent, malformed, stale, conflicting, unresolved, and unsupported registry states SHALL remain distinct in results and coverage.

#### Scenario: Two rules conflict
- **WHEN** equal-precedence rules define incompatible directions for one boundary
- **THEN** loading reports a conflict and neither rule silently wins

### Requirement: Adapter ranking is deterministic
Verified adapters SHALL participate in the documented ranking vector with explicit adapter count and cost and stable rule/declaration tie breaks.

#### Scenario: Two adapters verify
- **WHEN** both routes have otherwise equal application evidence
- **THEN** configured cost and stable identities determine deterministic order
