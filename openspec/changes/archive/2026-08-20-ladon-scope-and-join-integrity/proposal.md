## Why

Selected-scope reports currently confuse modules omitted from a bounded slice
with genuinely missing internal imports, rootless inventory analysis can acquire
an implicit reachability root, and composite findings can join unrelated signals
or sum unlike measures. These failures make otherwise useful architecture
evidence untrustworthy on large Lean repositories.

## What Changes

- Classify selected imports against the full discovered target inventory while
  preserving the existing scope planner and missing-import owner.
- Keep inventory analysis rootless unless the caller explicitly supplies a
  resolvable navigation root, and separate report anchors from analysis roots.
- Require every promoted composite to expose an inspectable structural join and
  resolvable evidence pointers.
- Preserve heterogeneous component measures instead of manufacturing a summed
  headline count.
- Add portable positive and intentional negative fixtures for scope boundaries,
  root semantics, join validity, aggregation, and evidence authority.

## Capabilities

### New Capabilities

- `ladon-scope-and-join-integrity`: Integrity checks over existing scope
  populations, import classifications, reachability views, and composite
  architecture findings.

### Modified Capabilities

None.

## Impact

The change integrates with the existing owners
`ladon-analysis-root-and-scope-contract`, `ladon-signal-correctness`, and
`ladon-architecture-correlator`; it does not replace their scope selection,
ownership, graph-metric, or finding-kind contracts. It affects run-context
inventory metadata, module-DAG boundary summaries, root-relative report fields,
composite correlation evidence, renderers, and portable regression fixtures.
Per the umbrella dependency ledger, this packet starts after
`ladon-report-coverage-and-snapshot-integrity#coverage-foundation` and enables the
declaration/audit integrity and analysis-inspection packets.
