## ADDED Requirements

### Requirement: Repo-Local Policy Workflow

Ladon SHALL provide a repeatable workflow for discovering, validating, and
reporting repo-local policy files without requiring temporary CLI-only policy
paths.

#### Scenario: discovered policy source is visible

- **WHEN** Ladon discovers a repo-local architecture or source-pattern policy
- **THEN** the report SHALL include the policy id and source path.

#### Scenario: missing project policy is explicit

- **WHEN** a run has no architecture policy available
- **THEN** Ladon SHALL emit an explicit skipped-policy status rather than
  silently omitting project-specific boundary checks.

#### Scenario: policy examples stay generic

- **WHEN** documentation or example policies are added
- **THEN** they SHALL use generic names or target-repo-owned examples rather
  than hard-coded analyzer knowledge of a private project.
