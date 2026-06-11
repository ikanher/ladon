## ADDED Requirements

### Requirement: Lean parser helper preserves imported scoped parser syntax

The Lean extraction backend SHALL preserve parser context introduced by earlier
`open` commands while parsing later commands in a file.

#### Scenario: imported scoped syntax after open scoped

- GIVEN an imported module defines scoped syntax
- AND a target file runs `open scoped` for that namespace
- WHEN the Lean parser helper parses later declarations using that scoped syntax
- THEN extraction SHALL succeed without requiring full command elaboration.

#### Scenario: parser-only boundary is preserved

- GIVEN the helper carries parser context across `open` commands
- THEN it SHALL NOT elaborate theorem bodies just to activate scoped notation.
