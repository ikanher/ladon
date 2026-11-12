# Spec Delta

## Purpose

Checked feasibility diagnostics for exact local assumption contexts. This capability retains exact evidence scope and explicit unresolved outcomes.

## ADDED Requirements

### Requirement: Exact context selection

A feasibility request SHALL bind the selected proof position to file/source digest, syntax span/position, goal ordinal and owner-qualified local identities, and identify the complete selected data/hypothesis/let context, fixed parameter assignments and quantifier policy. Declaration-level type extraction alone SHALL NOT qualify proof-position support. Unsupported dependencies SHALL remain explicit. It SHALL NOT silently drop a hypothesis or generalize a fixed parameter.

#### Scenario: Only one parameter value works

- **WHEN** a witness establishes feasibility at parameter zero
- **THEN** the result applies to that assignment and does not claim feasibility for every parameter

#### Scenario: Two positions in one proof

- **WHEN** two positions in the same declaration have different assumptions or derived local aliases
- **THEN** selection captures their distinct contexts, rejects cross-position receipt reuse and preserves each position’s transitive dependencies

#### Scenario: Fixed assignment changes feasibility

- **WHEN** the same captured context requires n = 0 and the request fixes n first to 0 and then to 1
- **THEN** the subjects and generated goals differ, the first admits a witness and the second admits a refutation, and the assignment is never silently existentialized

### Requirement: Independent inhabitation evidence

A witnessed result SHALL require a replayed proof that the selected context has an inhabitant. The generated goal SHALL exclude the hypotheses under test and all proof or local-value dependencies derived from them from the witness environment.

#### Scenario: Witness uses the assumption under test

- **WHEN** the proposed witness relies on the selected existence hypothesis or a downstream alias
- **THEN** the attempt is rejected or remains unresolved and receives no witnessed status

### Requirement: Checked inconsistency

An inconsistent result SHALL require replayed evidence that no assignment satisfies the exact selected context. Its proof SHALL be checked under the declared axiom policy; a failed search for an inhabitant SHALL NOT establish inconsistency.

#### Scenario: Two contradictory equalities

- **WHEN** the selected context requires the same natural number to equal zero and one
- **THEN** a checked refutation of its existential closure establishes context inconsistency

#### Scenario: Unknown inhabitant

- **WHEN** the bounded search finds no witness and no contradiction
- **THEN** the result remains unresolved

### Requirement: Conditional validity preserved

Feasibility findings SHALL remain separate from conditional proof validity and attributed source intent. Intentional impossible branches and discharged contradiction assumptions SHALL NOT automatically be labeled exposition errors.

#### Scenario: Legitimate contradiction proof

- **WHEN** an impossible temporary branch is used to discharge a negation
- **THEN** the report identifies its scope and preserves the checked proof without a false accusation

### Requirement: Qualified automatic proof route

Operational detection credit SHALL require an attempt from the frozen family tactic repertoire with no supplied answer term or case-specific dispatch, followed by successful independent replay and axiom checking. A tactic proof whose generated auxiliaries cannot be replayed SHALL remain an explicit checker failure. A successful caller-supplied replacement SHALL count only as validation. Qualification SHALL include the retained auxiliary-declaration regression and either a repaired replay route or a qualified general automatic alternative on the same generated goal.

#### Scenario: Tactic applies but auxiliary replay fails

- **WHEN** an automatic refutation elaborates but independent replay cannot resolve a generated auxiliary declaration
- **THEN** no inconsistency authority or operational detection credit is granted, and a later hand-supplied equality proof does not close the automatic-route gate

### Requirement: Feasibility evidence binding

Witness and contradiction receipts SHALL bind the same exact context and parameter policy, fresh source/environment identities, checker and execution bounds. Incompatible positive and negative receipts SHALL trigger evidence rejection rather than a combined verdict.

#### Scenario: Imported receipt changes one hypothesis

- **WHEN** a saved witnessed receipt is attached to a stronger context
- **THEN** the binding fails and the stronger context remains unchecked

