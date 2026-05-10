## ADDED Requirements

### Requirement: Ladon SHALL provide a project-local doc-hardening skill

Ladon SHALL include a project-local skill that guides documentation and comment
hardening for active Ladon code and docs.

#### Scenario: Skill explains when to use it

- **WHEN** an agent is asked to improve Ladon docs, comments, docstrings, or
  analyzer-facing prose
- **THEN** the skill description clearly triggers for that work
- **AND** the body gives a concise checklist for Ladon's clean-core support
  boundary

### Requirement: Ladon docs SHALL state operational responsibility before traceability

Public Ladon docs and module docstrings SHALL begin by explaining what the
component does now before describing future proof/witness/packet aspirations.

#### Scenario: Clean-core docs avoid overclaiming

- **WHEN** a public doc describes Ladon's current analyzer
- **THEN** it identifies implemented module-DAG behavior
- **AND** it explicitly marks proof graph, packet review, witness audit, and
  export-surface checks as future or unsupported unless implemented in active
  clean modules

### Requirement: Ladon comments SHALL be selective and non-obvious

Inline comments SHALL explain local invariants or analyzer seams that are easy
to misread, not restate obvious code.

#### Scenario: Comment explains a graph-direction seam

- **WHEN** code computes import edges or reachability
- **THEN** comments may explain the chosen edge direction or report semantics
- **AND** comments do not narrate routine loops, assignments, or simple
  conditionals

### Requirement: Ladon public contracts SHALL document inputs, outputs, and failures

Public dataclasses and nontrivial public functions SHALL document the contract
when names alone do not make the behavior clear.

#### Scenario: Root discovery contract is documented

- **WHEN** a function resolves a root file or discovers modules
- **THEN** its docstring states accepted input forms and the failure mode for
  ambiguous or missing roots

### Requirement: Doc hardening SHALL preserve code behavior

Documentation hardening SHALL NOT change analyzer semantics except for
documentation, comments, or wording.

#### Scenario: Validation remains green

- **WHEN** the doc-hardening pass is complete
- **THEN** tests, strict quality, compileall, build, and OpenSpec validation all
  pass
