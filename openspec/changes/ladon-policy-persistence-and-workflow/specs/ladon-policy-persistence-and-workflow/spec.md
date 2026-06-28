## ADDED Requirements

### Requirement: Repo-Local Policy Persistence

Ladon SHALL support committed repo-local policy files for architecture and
source-pattern review rules.

#### Scenario: discovered policy source appears in report

- **WHEN** Ladon discovers a repo-local policy file
- **THEN** the report SHALL include the policy id and source path.

#### Scenario: missing architecture policy is explicit

- **WHEN** no architecture policy is supplied or discovered
- **THEN** Ladon SHALL emit a skipped-policy report and finding.

#### Scenario: examples are generic

- **WHEN** example policy files are checked into Ladon
- **THEN** their names and patterns SHALL be generic or clearly target-owned,
  not analyzer hard-coding of a private project.
