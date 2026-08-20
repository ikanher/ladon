## ADDED Requirements

### Requirement: Root-Focused Graph Findings

Ladon SHALL derive concise findings from already-computed module and declaration
graph summaries.

#### Scenario: declaration fan-in hotspot

- GIVEN a declaration graph summary with a declaration fan-in at or above the
  configured threshold
- WHEN findings are summarized
- THEN Ladon SHALL emit a declaration fan-in hotspot finding.

#### Scenario: unresolved reference hotspot

- GIVEN a declaration graph summary with an unresolved candidate count at or
  above the configured threshold
- WHEN findings are summarized
- THEN Ladon SHALL emit an unresolved reference hotspot finding.

#### Scenario: text report shows findings

- GIVEN findings are present in the report payload
- WHEN the text renderer runs
- THEN the report SHALL include a findings section before detailed graph tables.
