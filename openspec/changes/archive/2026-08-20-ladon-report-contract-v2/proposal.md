## Why

The report has accumulated optional dictionaries whose sections disappear,
skip reasons lose their text, and schema changes still use the
`clean-core-1` label. Consumers need a typed, published, deterministic contract
before deeper declaration data is added.

## What Changes

- **BREAKING**: Introduce a `ladon-report-v2` contract with a published JSON
  Schema and explicit compatibility policy.
- Replace ad hoc top-level dictionaries at phase boundaries with typed report
  models and validated serialization.
- Keep every registered phase present with `complete`, `skipped`, `partial`, or
  `failed` status and preserve its textual reason and provenance.
- Require deterministic collection ordering and stable serialization when the
  caller does not supply a timestamp.
- Define additive extension points for optional witness, atlas, and elaborated
  declaration sections without silently changing authority.
- Generate compact text and complete JSON from the same validated report model.
- Provide v1 JSON fixture compatibility tests and a documented transition path
  rather than mutating `clean-core-1` in place; text remains a v2-model
  rendering.

## Capabilities

### New Capabilities

- `ladon-report-contract-v2`: Typed phase/result model, published schema,
  deterministic serialization, and compatibility rules for Ladon reports.

### Modified Capabilities

None.

## Impact

- Affected code: pipeline results, IR/report models, renderers, atlas/import
  readers, SQLite export, workflow diffing, fixtures, and documentation.
- Affected external consumers: report version detection and any code relying
  on absent optional keys or the old numeric skip-reason artifact.
- The change must land before the elaborated declaration surface is promoted.
