# Spec Delta

## Purpose

Check exact local relationships between interpreted informal arguments and
observed formal proof slices while preserving open implications and evidence scope.

## ADDED Requirements

### Requirement: Explicit many-to-many correspondence
A correspondence SHALL identify selected informal and formal nodes, the object translation, intended relationship, and required transport obligations. One-to-many and many-to-one mappings SHALL be supported without inferring proof-method equivalence from a common conclusion.

#### Scenario: Formal proof uses a different valid argument
- **WHEN** a formal slice establishes the interpreted endpoint by a different route
- **THEN** endpoint support and correspondence with the described method receive separate outcomes

### Requirement: Premise supply and conclusion transfer are checked separately
For a selected formal implication, the system SHALL generate exact obligations for supplying its premises from the interpreted original context and deriving the required original conclusion from its result. Dependent contexts and object transports SHALL retain their order and scope.

#### Scenario: Formal lemma requires an extra hypothesis
- **WHEN** the interpreted source does not supply one of the lemma's premises
- **THEN** the missing implication remains visible and the formal theorem's acceptance cannot discharge it automatically

#### Scenario: Formal conclusion is stronger in the needed direction
- **WHEN** a checked transport derives the original conclusion from the stronger formal result
- **THEN** the correspondence records that checked implication without treating the superficial statement difference as a fault

### Requirement: Original obligations cannot be repaired implicitly
Generated goals SHALL preserve the original interpreted context and exclude invented assumptions, the desired conclusion, unavailable self-dependencies, or unestablished predecessor claims. A proposed repair SHALL be a separate interpretation with separate evidence.

#### Scenario: Disputed premise is added as a local assumption
- **WHEN** a proof attempt closes only after assuming the disputed premise
- **THEN** the system records at most a conditional result for the revised context and leaves original premise establishment unresolved

### Requirement: Independent mathematical result dimensions
Results SHALL distinguish local conditional validity, establishment of premises, parent-claim support, interpretation fidelity, method correspondence, extraction coverage, and checker authority. Parent support SHALL require the actual needed links and providers, not merely matched reviewer labels.

#### Scenario: Valid conditional follows a false intermediate claim
- **WHEN** the last implication is valid under a premise that the original argument fails to establish
- **THEN** the conditional remains supported while premise establishment and parent support remain independently unestablished or refuted by their own evidence

### Requirement: Checked obligations and failed attempts retain distinct authority
Accepted obligation evidence SHALL come from the named checker on the exact generated goal under its recorded environment and trust policy. Rejection, residual goals, missing support, timeout, or unsupported extraction SHALL NOT become a counterexample or an accepted derivation.

#### Scenario: Candidate tactic fails to prove a true claim
- **WHEN** a supplied term is rejected for the selected original goal
- **THEN** the result records the failed attempt and an unresolved obligation rather than a false-claim verdict

### Requirement: Counterexamples satisfy the exact original obligation
A checked refutation SHALL establish every premise and falsify the conclusion of the exact interpreted obligation. Arithmetic replay, quantified refutation, source fidelity, and realization of abstract quantities SHALL remain separately identified with any incomplete links exposed.

#### Scenario: Numerical values violate an encoded assumption
- **WHEN** a proposed assignment falsifies the conclusion but violates a premise
- **THEN** it is reported outside assumptions and cannot close a refutation

#### Scenario: Analytic counterargument has no supported replay
- **WHEN** a reviewer supplies a continuity argument outside the available checker fragment
- **THEN** it remains attributed mathematical evidence unless a corresponding checked argument is actually executed

### Requirement: Checked links bind their complete inputs
Correspondence artifacts SHALL be native, bounded, and canonically identified, with references to exact interpretations, selected slices, object maps, contexts, attempts, and observations. Changed inputs SHALL invalidate affected checked links without upgrading unchanged historical receipts.

#### Scenario: Domain changes after successful checking
- **WHEN** an interpretation is widened from a restricted domain to a larger domain
- **THEN** the previous check remains historical evidence for its original domain and the new correspondence requires new obligations
