## ADDED Requirements

### Requirement: Declaration Name Family Groups

Ladon SHALL summarize similarly named declaration families using declaration
basename suffixes.

#### Scenario: suffix groups are emitted

- GIVEN declarations share the same suffix after the first underscore
- WHEN declaration graph analysis runs
- THEN the summary SHALL include a declaration family row for that suffix.

#### Scenario: text report renders declaration family groups

- GIVEN declaration family rows are present
- WHEN text rendering runs
- THEN the report SHALL include a `Declaration Name Families` section.

#### Scenario: large declaration families become findings

- GIVEN a declaration family contains at least three declarations
- WHEN findings are summarized
- THEN Ladon SHALL emit a declaration family hotspot finding.
