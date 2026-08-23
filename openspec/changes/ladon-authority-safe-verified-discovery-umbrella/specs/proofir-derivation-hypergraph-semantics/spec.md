## MODIFIED Requirements

### Requirement: Distinct bounded graph queries
Navigation path, complete derivation slice, satisfaction, alternatives, and SCC analysis SHALL use distinct schemas, finite caps, accurate nonclaims, and stack-safe traversal whose supported depth is governed by declared query bounds rather than host-language recursion limits.

#### Scenario: Complete slice for conjunctive step
- **WHEN** a complete slice is requested for C through a step requiring A and B
- **THEN** both premise branches appear or the result explicitly reports truncation

#### Scenario: Deep valid derivation
- **WHEN** satisfaction and complete-slice queries traverse a valid linear derivation deeper than Python's recursion limit but within declared bounds
- **THEN** both queries terminate from their owned iterative traversal without `RecursionError`

#### Scenario: Declared bound is reached
- **WHEN** a deep derivation exceeds a ProofIR depth, reference, step, premise, alternative, or result budget
- **THEN** the query returns the specified unknown or truncated result with the exact ProofIR bound and no interpreter-limit diagnostic

## ADDED Requirements

### Requirement: One authoritative slice traversal implementation
Complete derivation slicing SHALL have one production traversal implementation; superseded recursive and alternate dormant implementations SHALL be removed after differential contract fixtures pass.

#### Scenario: Implementation inventory is checked
- **WHEN** the maintained derivation source is scanned and the complete-slice suite runs
- **THEN** only the stack-safe production traversal is reachable or defined and all ordering, occurrence, residual, alternative, and truncation fixtures pass

### Requirement: Stack safety remains Ladon-owned
The authoritative traversal and its deep fixtures SHALL remain in Ladon/ProofIR-owned source and SHALL require neither Quux nor a Python recursion-limit change.

#### Scenario: Clean environment runs deep fixtures
- **WHEN** the deep satisfaction and slice suites run without Quux and with the default interpreter recursion limit
- **THEN** they pass using declared ProofIR budgets only
