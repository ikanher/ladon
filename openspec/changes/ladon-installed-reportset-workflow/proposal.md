## Why

Ladon already contains atlas export, SQLite, query, generic diff, reviewer-card,
and workflow implementations, but important operations are reachable only from
source-checkout scripts. A user of an installed wheel cannot complete the
report-to-review loop.

## What Changes

- Expose existing atlas export, SQLite derivation, canned query, generic diff,
  reviewer-card, and workflow operations through one supported installed CLI.
- Import the existing library functions; reduce checkout scripts to
  compatibility wrappers or retire them after a documented window.
- Consume bounded report projections, deterministic bundles, actionable
  evidence links, and audit rows without redefining their schemas.
- Preserve shared stdout/stderr and exit behavior, deterministic normalized
  outputs, explicit report-version dispatch, and clear unknown-major errors.
- Distinguish highlighted atlas nodes from total inventory counts.

## Capabilities

### New Capabilities

- `ladon-installed-reportset-workflow`: Installed end-to-end report, bundle,
  atlas, query, diff, card, and workflow operations.

### Modified Capabilities

None. Existing atlas/report-set modules and completed packets remain the sole
owners of algorithms and schemas.

## Impact

- Start after `ladon-large-inventory-scale-contract`,
  `ladon-actionable-findings-workflow`, and
  `ladon-analysis-runsets-and-bundles`; integrate with
  `ladon-lean-audit-command-surface`.
- Existing owners reused: `ladon-report-atlas-export`,
  `ladon-atlas-diff-mini`, `ladon-atlas-sqlite-query-mini`, and
  `ladon-atlas-review-workflow-and-bridge-cards`.
- Affected code: CLI registration, package entrypoints/resources, thin script
  wrappers, installed-candidate tests, and documentation.
- Excluded work: reimplemented atlas logic, semantic theorem comparison,
  automatic Git-ref orchestration, graph databases, dashboards, or generated
  explanations. `ladon-theorem-surface-changelog` remains the comparator owner.
