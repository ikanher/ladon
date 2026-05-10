## ADDED Requirements

### Requirement: Composite Architecture-Pressure Findings

Ladon SHALL emit deterministic composite findings when multiple graph signals
co-occur strongly enough to warrant architecture review.

#### Scenario: composite finding cites component signals

- GIVEN module and declaration graph summaries with correlated architecture
  pressure signals
- WHEN findings are summarized
- THEN Ladon SHALL emit composite findings with a `component_signals` list.

#### Scenario: no defect claim

- GIVEN a composite finding is emitted
- WHEN its message is rendered
- THEN the message SHALL frame the issue as architecture pressure or review
  scope, not as a proven bug.

#### Scenario: missing signals remain non-blocking

- GIVEN only one side of a composite signal is present
- WHEN findings are summarized
- THEN Ladon SHALL not emit the corresponding composite finding.
