## ADDED Requirements

### Requirement: Ladon SHALL define backend-agnostic declaration IR

Ladon SHALL provide a declaration-level IR that can be populated by text,
Lean-native, or future cached extraction backends.

#### Scenario: Declaration carries ownership and references

- **WHEN** a declaration is represented in Ladon IR
- **THEN** it records its declaration name, owning module, optional kind, and
  reference candidates
- **AND** pure analysis code can consume it without invoking Lean or reading the
  filesystem

### Requirement: Ladon SHALL summarize exact declaration-reference graphs

Ladon SHALL provide a pure analysis pass that builds declaration edges only for
references that exactly match known declaration names.

#### Scenario: Known references become edges

- **WHEN** declaration `A.x` references `A.y` and `A.y` exists in the input
- **THEN** the declaration graph contains an edge from `A.x` to `A.y`
- **AND** `A.y` receives fan-in from `A.x`

#### Scenario: Unknown references stay unresolved

- **WHEN** a reference candidate does not exactly match any known declaration
- **THEN** it is counted as unresolved
- **AND** no graph edge is fabricated

### Requirement: Ladon SHALL report declaration reachability from selected roots

Ladon SHALL summarize which known declarations are reachable by following exact
reference edges from selected root declarations.

#### Scenario: Root reachability is explicit

- **WHEN** selected roots are supplied
- **THEN** the summary lists chosen roots and counts declarations not reachable
  from them
- **AND** absent requested roots are ignored rather than fabricated
