## Why

Owner review currently mixes authored target declarations, imported
dependencies, compiler-generated names, and project-generated table families.
That lets synthetic and repetitive populations dominate rankings while hiding
which evidence actually belongs to the selected project.

## What Changes

- Classify included rows as target-owned, imported, compiler-generated,
  project-generated, or explicitly unclassified.
- Accept inspectable versioned repository policy for project-generated
  families, including stable family identities and provenance.
- Make every population-sensitive metric state its numerator, denominator,
  exclusions, and selected population.
- Add family-collapsed review rows while retaining raw members in the full
  projection.
- Reuse raw population labels and policy discovery from
  `ladon-signal-correctness-hardening`, and elaborated declaration identity and
  generated attribution from `ladon-elaborated-declaration-surface`.

## Capabilities

### New Capabilities

- `ladon-project-ownership-and-generated-calibration`: Explicit ownership and
  generation populations, policy provenance, calibrated metrics, and
  generated-family aggregation.

### Modified Capabilities

None. Existing text and Lean authority remain unchanged by classification.

## Impact

- Affected code: project policy loading, module/declaration classification,
  metric population adapters, family aggregation, rendering, and fixtures.
- Downstream changes enabled: actionable finding ranking and audit-command
  subject ownership.
- Excluded work: target-specific `Data` or `Row` hard-coding, source rewriting,
  generator correctness/freshness claims, and removal of raw evidence.
- Classification never upgrades lexical evidence, asserts proof correctness,
  or introduces caller-specific behavior.
