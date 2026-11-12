# Spec Delta

## Purpose

Typed operation observations and checked source-attributed existence/property obligations. This capability retains exact evidence scope and explicit unresolved outcomes.

## ADDED Requirements

### Requirement: Typed operation identity

An operation observation SHALL retain its elaborated declaration, instantiated type, instance arguments and relevant coercions in the exact source context. Unsupported operations SHALL remain explicit rather than inheriting a familiar operation's semantics.

#### Scenario: Overloaded subtraction

- **WHEN** the prose interpretation elaborates subtraction on naturals while the formal counterpart uses integers
- **THEN** the report preserves both operations and requires the requested transport property rather than treating the notation as identical

### Requirement: Attributed operation expectations

Existence, membership, nonzero guards and operation-preservation properties SHALL be explicit source-attributed expectations. Adapter matching SHALL NOT invent an informal expectation or treat every total operation as an error.

#### Scenario: Total default is intended

- **WHEN** the source explicitly allows the natural infimum default on an empty set
- **THEN** the operation is recorded without an unsupported accusation of missing existence

### Requirement: Original property obligations

An admitted adapter SHALL generate the exact intended property under the original context and separate any proposed additional premises. A returned formal value SHALL NOT discharge an existence or membership obligation by itself.

#### Scenario: Empty-set infimum

- **WHEN** the source claims that its selected natural infimum belongs to an empty set
- **THEN** a checked negation of that membership establishes failure of the attributed property although the infimum expression is well typed

#### Scenario: Nonempty-set control

- **WHEN** the original context proves nonemptiness and the library supplies the relevant infimum property
- **THEN** checked evidence supports that property without adding an unstated premise

### Requirement: Conservative adapter registry

Adapters SHALL have versioned applicability conditions, exact subject binding and explicit unsupported cases. Initial supported behavior SHALL include Nat/Int subtraction transport and natural-set infimum existence/membership; broader operators SHALL require separately tested adapters.

#### Scenario: Unknown user-defined selector

- **WHEN** a function named minimum uses an unsupported representation
- **THEN** the result is unsupported and does not apply a built-in infimum rule by name

### Requirement: Independent checked semantics

Property proofs and refutations SHALL use fresh Lean completion, replay and axiom checks. A finite numerical example SHALL support only its bound witness or checked counterexample, never universal equivalence.

A refutation SHALL concern the complete original proposition with its quantifiers and premises preserved. The checked replay target SHALL establish its negation or a counterexample satisfying the original premises. A negative conclusion proved under local hypotheses SHALL retain that conditional scope and SHALL NOT alone establish a refutation of the original universal conditional.

#### Scenario: Both local polarities follow from impossible premises

- **WHEN** completion proves both `H → Q` and `H → ¬ Q` with contradictory H
- **THEN** both results remain conditional facts and neither alone refutes the original proposition `H → Q`

#### Scenario: Counterexample satisfies the original premises

- **WHEN** independently checked evidence establishes `H a ∧ ¬ Q a` for the bound assignment a
- **THEN** it may support refutation of `∀ x, H x → Q x` with the assignment, original premises and replayed target retained

#### Scenario: Subtraction transport fails at two and three

- **WHEN** a checked counterexample separates natural truncated subtraction from the attributed integer operation
- **THEN** the report identifies that failed transport while preserving valid controls under an explicit order guard

### Requirement: Context and search limits

Operation checks SHALL retain exact assumption scope, source fidelity, resource limits and unresolved outcomes. Contradictory contexts SHALL remain visible through feasibility evidence when available.

#### Scenario: Property proved in impossible context

- **WHEN** a selector property is checked under contradictory premises
- **THEN** conditional support is retained and is not promoted to an inhabited or unconditional existence claim

