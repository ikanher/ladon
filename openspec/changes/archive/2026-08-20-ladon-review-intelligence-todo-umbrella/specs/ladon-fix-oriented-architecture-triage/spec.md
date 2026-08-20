## ADDED Requirements

### Requirement: Fix-Oriented Architecture Triage

Ladon SHALL attach review-oriented suggested actions to policy and architecture
findings when source evidence and policy context support a likely next step.

#### Scenario: direct peer import has action context

- **WHEN** a direct forbidden peer import is reported
- **THEN** Ladon SHALL include source location, group pair, context class, and a
  suggested review action.

#### Scenario: text report prioritizes summaries

- **WHEN** policy findings are rendered as text
- **THEN** pair summaries and top offending files SHALL appear before full raw
  finding counts.

#### Scenario: suggestions do not claim automatic correctness

- **WHEN** Ladon suggests extraction, bridge treatment, facade cleanup, obsolete
  import removal, or generator cleanup
- **THEN** the suggestion SHALL be phrased as review guidance, not an automatic
  proof of the correct refactor.
