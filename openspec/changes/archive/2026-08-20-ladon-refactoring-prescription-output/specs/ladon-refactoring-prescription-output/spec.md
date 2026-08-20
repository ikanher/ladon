## ADDED Requirements

### Requirement: Prescription taxonomy
The system SHALL emit refactoring prescription rows using a stable action
taxonomy.

#### Scenario: Core boundary violation
- **WHEN** architecture policy evidence reports a core-looking direct peer import
- **THEN** Ladon emits a high-priority prescription with the source evidence

### Requirement: Prescriptions are review guidance
The system SHALL state that prescriptions are review directions and not
automatic edits or proof of correctness.

#### Scenario: Prescription rendering
- **WHEN** a prescription appears in output
- **THEN** it includes evidence, confidence, priority, and nonclaim text
