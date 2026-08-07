## Why

During structure construction, users need to know which declarations consume an
authority and which fields already have usable suppliers. Existing forward
dependency reports do not expose constructor coverage or circular certificate seams.

## What Changes

- Add reverse project-owned consumer search with exact source locations and
  elaborated dependency authority.
- Enumerate structure fields and compare their instantiated types with declarations
  available in the active proof scope.
- Classify field suppliers as exact, stronger-hypothesis, restricted-range,
  adapter-dependent, or unmatched.
- Distinguish qualitative adapter fields from quantitative-bound fields.
- Detect when a proposed constructor still accepts a premise equivalent to the
  field it purports to derive, and label this as review evidence rather than proof.

## Capabilities

### New Capabilities

- `ladon-declaration-consumers-and-constructor-coverage`: Reverse consumers,
  field-by-field constructor coverage, and certificate-leakage review diagnostics.

### Modified Capabilities

None.

## Impact

- Adds reverse index queries, structure/constructor normalization, coverage matrices,
  quantitative/qualitative field metadata, leakage diagnostics, and source-linked
  CLI/JSON outputs.
