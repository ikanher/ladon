## ADDED Requirements

### Requirement: Docs Describe Current Ladon Signals

Ladon documentation SHALL describe newly implemented report signals.

#### Scenario: unresolved classes are documented

- GIVEN a user reads Ladon docs or skill guidance
- WHEN they interpret declaration reports
- THEN unresolved reference classes and actionable unresolved rows SHALL be
  mentioned.

#### Scenario: declaration families are documented

- GIVEN a user reads Ladon docs or skill guidance
- WHEN they inspect repeated proof skeletons
- THEN declaration name families SHALL be mentioned.
