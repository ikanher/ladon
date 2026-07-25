## ADDED Requirements

### Requirement: Optional compact ProofIR bridge
Ladon SHALL provide an optional bridge that combines a Ladon report with a
compact ProofIR bridge index without importing raw ProofIR dialects into the
analysis core.

#### Scenario: Compact bridge inputs are joined
- **WHEN** a caller supplies a Ladon report and a valid compact ProofIR bridge index
- **THEN** the bridge emits structured joins, reviewer cards, diagnostics, and trust rules without mutating either input

#### Scenario: ProofIR input is absent
- **WHEN** no ProofIR index is supplied
- **THEN** the bridge emits a valid empty optional report and does not invent external evidence

#### Scenario: ProofIR input is malformed
- **WHEN** the supplied external payload is not a supported compact bridge index
- **THEN** the bridge emits a malformed-index diagnostic instead of promoting its contents

### Requirement: Evidence-bounded bridge joins
Bridge joins SHALL expose their match kind and confidence and SHALL preserve
ProofIR status as quoted external context rather than Ladon-established truth.

#### Scenario: Source hash and declaration match
- **WHEN** source hash and declaration identity match
- **THEN** the bridge emits a high-confidence attachment and states that attachment confidence is not proof authority

#### Scenario: Name-only match
- **WHEN** only a declaration basename matches
- **THEN** the bridge emits a low-confidence warning-only join

#### Scenario: External claim status is attached
- **WHEN** a joined ProofIR claim carries status or authority metadata
- **THEN** the reviewer card preserves it as quoted external evidence and does not label it established by Ladon
