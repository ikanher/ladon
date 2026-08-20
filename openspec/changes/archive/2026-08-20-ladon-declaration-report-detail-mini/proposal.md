## Why

Declaration graph reports now compute useful data, but the text report only
shows counts. Reviewers need the first actionable triage rows: top fan-in,
top fan-out, and frequent unresolved reference candidates.

## What Changes

- Add unresolved-reference frequency rows to declaration graph summaries.
- Render top declaration fan-in/fan-out and unresolved candidates in text.
- Keep JSON additive and tests synthetic.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `ladon-declaration-graph`: reports include actionable declaration graph
  triage rows.

## Impact

- Affected code: `src/ladon/analysis/declaration_graph.py`,
  `src/ladon/render.py`.
- Affected tests: declaration graph summary and text rendering.
