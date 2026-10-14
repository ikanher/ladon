## Purpose

Preserve the declared mathematical types and operations when an authored prose interpretation is lowered into an actual Lean proposition for checking.

## ADDED Requirements

### Requirement: Use-site types govern expression lowering
Supported lowering SHALL preserve each declared operator's instantiated type, operand types, explicit casts, and result type at its actual application. Numeral-only subexpressions SHALL NOT silently default to an incompatible type. Unsupported type inference SHALL remain an explicit incomplete outcome.

#### Scenario: Real fractional endpoint
- **WHEN** an interpretation declares real division and the endpoint 41/20
- **THEN** the checked endpoint is the real rational 41/20, not the natural quotient 2 coerced to Real
- **AND** a separately checked declaration type cannot substitute for validation of the actual application

#### Scenario: Intentional natural division
- **WHEN** an interpretation explicitly requests natural-number division followed by a real cast
- **THEN** its truncated quotient is preserved and remains distinct from real division

#### Scenario: Nested operations and incompatible types
- **WHEN** a nested numeral-only application conflicts with its declared operand or result type
- **THEN** the conflict is diagnosed before its replay can support the advertised interpretation

### Requirement: Actual elaboration is reviewable and bound
A checking result SHALL bind the typed structured interpretation to the observed elaborated proposition and its environment. Review exports SHALL expose actual operand/operator typing and the original source. Agreement of emitted text or a typing-only tautology SHALL NOT establish source fidelity or mathematical truth.

#### Scenario: Wrong but provable encoding
- **WHEN** an accidentally weakened encoded proposition is provable while its types disagree with the structured interpretation
- **THEN** its proof cannot support that interpretation and the discrepancy is visible in the review input

#### Scenario: Well-typedness probe
- **WHEN** a goal of the form P implies P is accepted
- **THEN** it is counted as a typing probe and is not counted as proof of P or a distinct validated prose assertion

### Requirement: Semantic profile changes preserve historical evidence
Changed lowering semantics SHALL have explicit profile and implementation identities. Old artifacts and first reviews SHALL remain unchanged; new checks and source-fidelity judgments SHALL require new bound records. Unknown profiles SHALL fail explicitly.

#### Scenario: Replaying a corrected numeric interpretation
- **WHEN** a real-typed interpretation replaces a historically accepted natural-division encoding
- **THEN** it receives fresh checks and review while the original record and its mistaken first assessment remain available

### Requirement: Literal families retain distinct semantics
The admitted numeric fragment SHALL preserve positive and negative integer literals, rational and real fractions, typed zero, and explicit conversions across supported domains. It SHALL retain existing expression and process bounds and SHALL reject malformed or unsupported encodings without inventing a type.

#### Scenario: Rational and integer controls
- **WHEN** identical digit spellings occur in Nat, Int, Rat, and Real contexts
- **THEN** each actual elaboration matches its declared context and cross-domain substitutions require explicit justified conversion
