## ADDED Requirements

### Requirement: OpenSpec Status Hygiene

Ladon SHALL provide a deterministic check for OpenSpec packet metadata status
that disagrees with task checklist evidence.

#### Scenario: completed checklist marked active

- GIVEN a change has a `.openspec.yaml` with `status: active`
- AND its `tasks.md` contains only checked checklist items
- WHEN OpenSpec hygiene analysis runs
- THEN Ladon SHALL report the change as status drift.

#### Scenario: partial checklist remains active

- GIVEN a change has at least one unchecked checklist item
- WHEN OpenSpec hygiene analysis runs
- THEN Ladon SHALL NOT report active metadata as completed-active drift.

#### Scenario: safe metadata normalization

- GIVEN a change is reported as completed-active drift
- WHEN safe normalization runs
- THEN only the metadata `status:` line SHALL be updated to `completed`.
