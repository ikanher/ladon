# Spec Delta

## ADDED Requirements

### Requirement: Rational branch Lean obligations
The rational-branch proof route SHALL generate obligations from the validated branch, base goal and exact assignment. It SHALL preserve the bounded rational AST's arithmetic and comparison semantics and reject any request it cannot represent faithfully. Generated goals SHALL be derived internally; caller-written goal text SHALL NOT be accepted.

#### Scenario: Supported rational assignment
- **WHEN** a branch and assignment use supported rational expressions with defined arithmetic
- **THEN** the route regenerates one or more Lean obligations that encode the exact checked predicates and conclusion for that assignment

#### Scenario: Undefined or unsupported arithmetic
- **WHEN** an expression divides by a value that evaluates to zero, or uses an unsupported AST operation
- **THEN** the route reports a bounded unsupported/rejected result and generates no Lean goal or checked support

#### Scenario: Rational normalization is unavailable
- **WHEN** the exact Lean workspace lacks the required Mathlib rational normalization support
- **THEN** the route reports unsupported before publishing a checked rational-branch result

### Requirement: Branch-bound proof replay
Every rational-branch plan and checked receipt SHALL bind the branch identity and kind, source-span identities, base and derived goal identities, exact assignment, generated Lean goal identities and checker identity. A checked receipt and its per-goal ProofIR check-run artifacts SHALL bind the captured compiled-module inventory used during replay. Rechecking SHALL regenerate the obligations and reject stale or mismatched bindings. Unauthenticated caller-supplied cache data SHALL NOT authorize checked support or skip fresh Lean replay.

#### Scenario: Branch changes while goal text stays the same
- **WHEN** a caller replays a receipt with a different branch identity, base goal, assignment or cited source
- **THEN** the regenerated plan or receipt binding differs and no old checked support is reused

#### Scenario: Caller supplies a forged cache receipt
- **WHEN** a caller supplies cache data with self-asserted accepted, replayed and trusted fields
- **THEN** the route performs fresh bounded Lean replay and publishes no support if that replay does not complete and pass trust validation

#### Scenario: Compiled inventory changes during a multi-goal check
- **WHEN** the captured compiled-module inventory differs between generated-goal checks
- **THEN** the route reports stale input and publishes no checked support

### Requirement: Rational proof scope
A Lean-checked rational-branch result SHALL report only the checked proposition for the encoded assignment and branch. It SHALL preserve source-formula fidelity as unverified and SHALL NOT report a result as proof or refutation of the original prose or theorem.

#### Scenario: Checked repair branch
- **WHEN** Lean checks obligations generated from a proposed-repair branch
- **THEN** the result remains labeled as a proposed repair and does not count as support for or refutation of the original claim

#### Scenario: Checked source-cited branch
- **WHEN** Lean checks obligations generated from a source-cited AST
- **THEN** the result records machine-checked rational obligations while retaining unverified source formula fidelity
