## ADDED Requirements

### Requirement: Generated Artifact Attribution

Ladon SHALL attribute generated-module pressure and generated duplicate imports
to likely generator families when source/path evidence supports a generic
classification.

#### Scenario: duplicate generated imports are grouped

- **WHEN** duplicate imports occur in generated modules
- **THEN** Ladon SHALL group the duplicate targets by likely generator family
  and target module.

#### Scenario: generated pressure is separated from handwritten pressure

- **WHEN** module fan-in, fan-out, or large-file tables are produced
- **THEN** Ladon SHALL expose generated-aware and handwritten-focused views so
  generated artifacts do not hide owner-file pressure.

#### Scenario: generator attribution remains heuristic

- **WHEN** a generated-family cleanup hint is emitted
- **THEN** the report SHALL expose the source evidence and SHALL NOT claim the
  generator is proven incorrect.
