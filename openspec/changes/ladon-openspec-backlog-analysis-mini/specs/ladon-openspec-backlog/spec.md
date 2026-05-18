## ADDED Requirements

### Requirement: OpenSpec Backlog Analysis

Ladon SHALL summarize operational hygiene findings over OpenSpec change
directories.

#### Scenario: missing automation

- GIVEN an OpenSpec change has no `automation.json`
- WHEN backlog analysis runs
- THEN Ladon SHALL report a `missing_automation` finding for that change.

#### Scenario: missing validation command

- GIVEN an OpenSpec change has automation commands
- AND none of them include `openspec validate`
- WHEN backlog analysis runs
- THEN Ladon SHALL report a `missing_validation_command` finding.

#### Scenario: stale child reference

- GIVEN an OpenSpec change has a file under `children/child-id.md`
- AND `openspec/changes/child-id` does not exist
- WHEN backlog analysis runs
- THEN Ladon SHALL report a `stale_child_reference` finding.
