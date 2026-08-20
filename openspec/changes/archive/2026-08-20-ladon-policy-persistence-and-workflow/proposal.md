## Why

Policy-backed Ladon runs are useful only when the project policy is durable and
discoverable. Temporary CLI policy files make smoke results hard to reproduce
and make CI integration fragile.

## What Changes

- Add a repo-local policy workflow for `.ladon/architecture-policy.json` and
  `.ladon/source-pattern-policy.json`.
- Validate discovered policy sources and expose policy ids/source paths in
  reports.
- Add generic examples and docs that keep project-specific names outside Ladon.

## Capabilities

### New Capabilities

- `ladon-policy-persistence-and-workflow`: Repo-local policy discovery,
  validation, examples, and visible report source metadata.

### Modified Capabilities

None.

## Impact

- Affected code: CLI/pipeline policy discovery, report metadata, tests, docs.
- Affected workflow: target repos can commit `.ladon/` policies and run Ladon
  without temp policy paths.
