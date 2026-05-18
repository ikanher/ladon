## ADDED Requirements

### Requirement: Named Calibration Suites

Ladon SHALL allow calibration regression checks to target different report
layouts.

#### Scenario: root-matrix suite is selected

- GIVEN generated reports from the maintained root matrix
- WHEN the calibration regression script is run with `--suite root-matrix`
- THEN it SHALL evaluate root-matrix expectations instead of live-run
  expectations.

#### Scenario: live suite remains default

- GIVEN no suite argument is provided
- WHEN the calibration regression script runs
- THEN it SHALL evaluate the existing live preregistration expectations.

### Requirement: Root Matrix Predicates

Ladon SHALL include predicates for root-scope classes and review-region labels.

#### Scenario: root-scope classification predicate

- GIVEN a report contains a `root_scope_pressure` finding with embedded
  `root_scope.classification`
- WHEN the expected class matches
- THEN the predicate SHALL pass.

#### Scenario: review-region predicate

- GIVEN a report contains review regions
- WHEN the expected region kind is present with enough signals
- THEN the predicate SHALL pass.
