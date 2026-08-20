## MODIFIED Requirements

### Requirement: Ladon SHALL normalize parser-helper JSON into stable module IR

Ladon SHALL convert parser-helper imports and declaration-like commands into
stable IR without exposing parser-helper internals to pure analysis passes.
Parser-helper declaration reference candidates SHALL be carried as
`LeanDeclaration.references` when available.

#### Scenario: Parser output contains imports and declarations

- **WHEN** parser-helper JSON contains header imports and declaration-like
  commands
- **THEN** normalized `LeanModule.imports` preserves imported module names
- **AND** normalized `LeanModule.declarations` contains declaration full names
  when available
- **AND** normalized `LeanDeclaration` rows preserve declaration kind and
  reference candidates
