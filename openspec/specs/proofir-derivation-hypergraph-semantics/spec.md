## Purpose

Define portable, bounded derivation-hypergraph semantics that preserve
conjunctive premises, alternative derivations, failed attempts, and explicit
recursion without turning navigation paths into proof claims.

## Requirements

### Requirement: Explicit derivation steps
A derivation step SHALL contain an ordered set of premise statement references, one conclusion statement reference, a rule reference, substitutions, local context, and supporting observation references.

#### Scenario: Binary theorem application
- **WHEN** a theorem application requires premises A and B to conclude C
- **THEN** one step records both A and B as conjunctive premises and C as its conclusion

### Requirement: AND premises and OR alternatives
Premises within one step SHALL have AND semantics, while multiple steps with the same conclusion SHALL be represented as OR alternatives.

#### Scenario: Two proofs of C
- **WHEN** steps S1 and S2 both conclude C
- **THEN** alternative analysis reports two choices without merging their premise sets

### Requirement: Separate derivations plans and attempts
Accepted derivations, advisory plans, and failed attempt logs SHALL use distinct artifact kinds and SHALL NOT share a scalar status to imply equivalence.

#### Scenario: Candidate application is rejected
- **WHEN** Lean rejects a proposed candidate application
- **THEN** it appears in an attempt log and not in an accepted derivation

### Requirement: Graph integrity and recursion policy
Acyclic derivation artifacts SHALL reject cycles; recursive graphs SHALL declare explicit SCC semantics and expose their components.

#### Scenario: Cyclic claimed DAG
- **WHEN** a native derivation contains a directed cycle but claims acyclic semantics
- **THEN** semantic validation rejects it with cycle evidence

### Requirement: Distinct bounded graph queries
Navigation path, complete derivation slice, satisfaction, alternatives, and SCC analysis SHALL use distinct schemas, finite caps, and accurate nonclaims.

#### Scenario: Complete slice for conjunctive step
- **WHEN** a complete slice is requested for C through a step requiring A and B
- **THEN** both premise branches appear or the result explicitly reports truncation

### Requirement: Portable owned algorithms
Graph and hypergraph algorithms SHALL be implemented in ProofIR/Ladon-owned code and portable tests SHALL pass without importing Quux.

#### Scenario: Clean environment
- **WHEN** SCC and slice tests run without a Quux checkout
- **THEN** all algorithms and fixtures remain available
