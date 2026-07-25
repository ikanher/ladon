## Why

The large-repository text report found useful architecture pressure but omitted
most rows without an installed lookup path, while owner output mixed global and
local findings. Existing findings need resolvable evidence and deterministic
inspection before Ladon adds more signal families.

## What Changes

- Give every promoted existing finding a wording-independent stable ID,
  finalized count, scope, owner relevance, evidence references, and separate
  severity, confidence, priority, and authority fields.
- Add installed ordinary CLI list, filter, and show operations over a report or
  bundle, including lookup by ID and bounded suggested next commands.
- Rank owner and closure evidence before optional inventory context and make
  text, JSON, phase, atlas, and bundle counts agree.
- Reuse existing finding kinds, severities, stable keys, prescriptions,
  authority labels, and source evidence; consume explicit scope populations,
  ownership calibration, and the bounded report projection contract.

## Capabilities

### New Capabilities

- `ladon-actionable-findings-workflow`: Stable promoted-finding evidence,
  owner-relevant ranking, deterministic filtering, and public CLI lookup.

### Modified Capabilities

None. This change improves navigation and accounting for existing findings; it
does not define a new smell taxonomy.

## Impact

- Start after `ladon-analysis-root-and-scope-contract` and
  `ladon-project-ownership-and-generated-calibration`; integrate with
  `ladon-large-inventory-scale-contract`.
- Affected code: finding finalization, evidence registry, ranking, report
  rendering, CLI inspection, atlas adapters, and fixtures.
- Downstream change enabled: `ladon-installed-reportset-workflow`.
- Excluded work: new finding families, automatic repairs, fabricated source
  ranges, authority promotion, or unbounded default text.
- Suggested actions are ordinary public CLI commands, never caller-specific
  commands or generated explanations.
