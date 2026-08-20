## ADDED Requirements

### Requirement: Lean elaborates semantic queries
The verifier SHALL elaborate the pattern and repeatable assumptions once in the requested module environment, with `_` producing anonymous pattern metavariables.

#### Scenario: Wildcard pattern is submitted
- **WHEN** a pattern contains anonymous wildcards
- **THEN** the response includes the elaborated pattern, wildcard identities, fingerprints, shape, and environment generation

### Requirement: Candidate checks are batched and authoritative
The verifier SHALL check a bounded candidate list in one helper request using declared syntactic, definitional-reducible, symmetry, and optional bounded semi-reducible passes.

#### Scenario: Symmetric equality applies
- **WHEN** direct conclusion matching fails but reversing `Eq` or `Iff` succeeds
- **THEN** the candidate is returned with match class `symmetry` and Lean verification authority

### Requirement: Unresolved evidence is separated
The verifier MUST report candidate-binder substitutions, residual proof premises, unresolved instances, unresolved non-proof terms, adapters, stale candidates, and exact failure diagnostics as separate fields.

#### Scenario: Candidate needs an inequality and an instance
- **WHEN** its conclusion matches but those obligations remain
- **THEN** the inequality is a residual proof premise and the instance appears separately as unresolved instance evidence

### Requirement: Verification is finitely supervised
Every request SHALL enforce candidate, heartbeat, recursion, deadline, diagnostic, and output-byte limits and report reached bounds.

#### Scenario: Candidate exceeds limits
- **WHEN** Lean exhausts the configured verification budget
- **THEN** the row is bounded/unavailable with exact limit evidence and is not labelled verified
