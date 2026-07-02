## Why

Ladon findings are more useful when they point to concrete refactoring review
actions instead of remaining as unrelated warning rows.

## What Changes

- Add a stable refactoring prescription taxonomy.
- Map architecture, generated-artifact, large-module, import-diet, proof-xray,
  and proof-surface evidence to prioritized prescription rows.
- Render prescriptions in JSON/text output with confidence and nonclaim text.

## Capabilities

### New Capabilities

- `ladon-refactoring-prescription-output`: Prioritized refactoring prescriptions
  derived from existing review evidence.

### Modified Capabilities

None.

## Impact

- Affected code: prescription analysis, pipeline, rendering, docs, and tests.
