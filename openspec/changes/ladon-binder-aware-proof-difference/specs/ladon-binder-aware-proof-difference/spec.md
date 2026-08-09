## ADDED Requirements

### Requirement: Explain resolves and peels bounded candidate evidence
`explain` SHALL resolve a unique candidate from a fresh index or accept an explicitly supplied signature, separate ordered binders from its conclusion, and preserve binder name, info, type, premise status, and authority.

#### Scenario: Candidate theorem has parameters and hypotheses
- **WHEN** its peeled conclusion matches the requested goal
- **THEN** the result identifies parameter substitutions separately and returns unmatched hypotheses as residual premises

### Requirement: Lexical normalization is shared and conservative
Conclusion comparison SHALL share qualification, whitespace, parenthesis, Unicode/ASCII arrow, and implicit-argument normalization with type search and SHALL retain original text and normalization identity.

#### Scenario: Representations normalize to the same lexical conclusion
- **WHEN** only supported representation differences separate goal and conclusion
- **THEN** the result reports a lexical match with residuals and does not claim Lean verification

### Requirement: Inconclusive lexical analysis is not negative proof evidence
Parser failure, ambiguity, unsupported syntax, unresolved candidate identity, and normalization uncertainty SHALL produce `indeterminate-lexical`; `not-applicable` SHALL require an established structural contradiction or Lean verification.

#### Scenario: Candidate syntax cannot be peeled safely
- **WHEN** lexical analysis reaches unsupported syntax
- **THEN** the response reports the unsupported boundary and MUST NOT classify the theorem as inapplicable

### Requirement: Suggestions remain one-level and authority-labeled
Residual-premise suggestions SHALL be finite SQLite shortlists with source, freshness, and `verification: not_requested`; they MUST NOT become discharged binders without Lean evidence.

#### Scenario: A residual has a lexical candidate
- **WHEN** one-level suggestions are enabled
- **THEN** the candidate appears as navigation evidence and the residual remains unresolved
