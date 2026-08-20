## ADDED Requirements

### Requirement: Configurable Lexical Audit Packs

Ladon SHALL support reusable, project-supplied source-pattern policies for
stale terms, local trust markers, TODO classes, banned prose, and anchored Lean
trust constructs without hard-coded project vocabulary.

#### Scenario: policy pack reports source matches

- **WHEN** a configured pattern matches source text
- **THEN** Ladon SHALL report pattern id, kind, severity, module, source path,
  line, generated status, and bounded sample text.

#### Scenario: zero-match policy still reports coverage

- **WHEN** a source-pattern policy is supplied and no rows match
- **THEN** Ladon SHALL report zero matches and per-pattern zero counts.

#### Scenario: project terms stay outside analyzer code

- **WHEN** stale names or local trust words are audited
- **THEN** they SHALL be supplied by policy files or fixtures rather than
  embedded in Ladon source code.
