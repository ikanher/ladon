## Why

Generated modules can dominate fan-in/fan-out and duplicate-import findings.
Reviewers need to know whether cleanup belongs in handwritten Lean or in the
generator that emitted the source.

## What Changes

- Attribute generated pressure and duplicate imports to likely generator
  families using source/path evidence.
- Group duplicate imports by generator family and target.
- Emit generator-cleanup hints without claiming generator correctness.

## Capabilities

### New Capabilities

- `ladon-generated-artifact-attribution`: Generated-family attribution for
  duplicate imports and generated graph pressure.

### Modified Capabilities

None.

## Impact

- Affected code: extraction tags, module DAG metadata, duplicate import rows,
  report rendering.
