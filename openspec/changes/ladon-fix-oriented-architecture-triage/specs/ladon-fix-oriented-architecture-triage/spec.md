## ADDED Requirements

### Requirement: Fix-Oriented Policy Summaries

Ladon SHALL summarize architecture policy violations in a way that helps
reviewers choose the next inspection target.

#### Scenario: direct finding includes source and action

- **WHEN** a forbidden direct import is reported
- **THEN** the finding SHALL include source module, target module, group pair,
  source path/line when available, policy context, and suggested action.

#### Scenario: text report is summary-first

- **WHEN** a text report includes policy findings
- **THEN** pair summaries, context summaries, and top offending files SHALL
  appear before raw finding counts.

#### Scenario: suggested action is review guidance

- **WHEN** a suggested action is emitted
- **THEN** it SHALL not claim the refactor is proven correct.
