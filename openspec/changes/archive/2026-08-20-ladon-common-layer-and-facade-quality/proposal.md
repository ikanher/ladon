## Why

Cross-family imports are often symptoms of missing lower layers, but pure
barrels and intentional shared foundations should not be treated like ordinary
implementation coupling.

## What Changes

- Broaden common-layer candidate detection through policy-selected modes.
- Rank common dependencies with confidence and importer/group evidence.
- Distinguish pure facades, generated aggregations, public root facades, and
  mixed barrel/theorem modules.

## Capabilities

### New Capabilities

- `ladon-common-layer-and-facade-quality`: Common-layer candidate ranking and
  facade subtype quality triage.

### Modified Capabilities

None.

## Impact

- Affected code: module DAG metadata, architecture policy common-dependency
  rows, findings, render output.
