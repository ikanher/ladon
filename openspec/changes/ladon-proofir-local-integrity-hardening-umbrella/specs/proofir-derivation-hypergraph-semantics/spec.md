## MODIFIED Requirements

### Requirement: Distinct bounded graph queries
Navigation path, complete derivation slice, satisfaction, alternatives, and SCC analysis SHALL use distinct schemas, finite caps, accurate nonclaims, and stack-safe traversal whose supported graph depth is governed by the declared query bounds rather than the host language recursion limit.

#### Scenario: Complete slice for conjunctive step
- **WHEN** a complete slice is requested for C through a step requiring A and B
- **THEN** both premise branches appear or the result explicitly reports truncation

#### Scenario: Deep derivation within declared bounds
- **WHEN** satisfaction and complete-slice queries traverse a valid linear derivation deeper than Python's default recursion limit but within every declared ProofIR budget
- **THEN** each query returns its specified complete or bounded result without raising a recursion error or other host-stack failure

#### Scenario: Deep derivation reaches a ProofIR bound
- **WHEN** a valid deep derivation exceeds a declared depth, node, edge, alternative, or output budget
- **THEN** the query terminates with the specified truncation or unknown result and attributes the exact ProofIR bound rather than an interpreter limit

## ADDED Requirements

### Requirement: Iterative traversal preserves derivation semantics
Stack-safe derivation traversal SHALL preserve deterministic AND-premise evaluation, stable OR-alternative choice, memoization, cycle and SCC policy, and canonical output ordering.

#### Scenario: Refactored shallow alternatives
- **WHEN** the iterative implementation evaluates the owned shallow, cyclic, alternative, and truncation corpus
- **THEN** it produces the same canonical semantic results as the frozen pre-refactor fixtures

