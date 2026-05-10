## ADDED Requirements

### Requirement: Text Report Groups Module DAG Details

The text report SHALL render module-DAG detail rows under explicit module
headings.

#### Scenario: module fan-in and fan-out are rendered

- GIVEN a module-DAG summary with top fan-in and fan-out rows
- WHEN the text renderer runs
- THEN the report SHALL include `Top Module Fan-In` and `Top Module Fan-Out`.

#### Scenario: facade modules are rendered

- GIVEN a module-DAG summary with facade modules
- WHEN the text renderer runs
- THEN the report SHALL include a facade modules section.

#### Scenario: unreachable modules are rendered

- GIVEN a module-DAG summary with modules not reachable from the chosen roots
- WHEN the text renderer runs
- THEN the report SHALL include an unreachable modules section.
