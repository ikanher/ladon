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

## Reconciliation Disposition

The generated-family attribution and duplicate-import requirements are shipped
and retain this packet as their historical source. The distinct defect where
generated importers inflate a table labeled handwritten is transferred to
`ladon-signal-correctness-hardening`, which owns population filters on both
importers and targets plus corrected labels. This packet is therefore
superseded-with-residuals rather than treated as the owner of that repair.
