## Why

The live Lean-backed owner trial ran for about 105 seconds, peaked near 8 GiB,
and exited with a partial report without stating the controlling failure
reason on stderr. Long analysis cannot be operable until progress, limits,
partial evidence, and cleanup are explicit and consistent.

## What Changes

- Add `auto`, `plain`, `json`, and `off` stderr-only progress modes.
- Add overall wall-time, peak-RSS, and report-byte limits alongside existing
  build and helper deadlines.
- Record stable failure classes, reasons, diagnostics, population completeness,
  cache decisions, and partial acceptance in every report representation.
- Add cancellation checkpoints for in-process discovery and rendering while
  reusing the existing process-group supervisor for descendants.
- Guarantee a concise Ladon-authored stderr cause for every operational exit 1
  and suppress or label metrics derived from incomplete populations.
- Reuse process/exit/channel semantics from `ladon-cli-execution-contract`,
  phase envelopes from `ladon-report-contract-v2`, and supervision/cache
  behavior from `ladon-lean-extraction-runtime-hardening`.

## Capabilities

### New Capabilities

- `ladon-partial-run-observability`: Progress, overall resource bounds,
  structured partial states, operational diagnostics, and cleanup behavior.

### Modified Capabilities

None. This change integrates existing CLI, report, and Lean-runtime owners
rather than defining a second supervisor, cache, or exit-code contract.

## Impact

- Affected code: CLI options, progress events, resource monitoring, phase
  adapters, cancellation checkpoints, rendering, and failure-path fixtures.
- Downstream changes enabled: scope planning, runsets, and the Lean audit
  command surface.
- Excluded work: implicit target builds, unbounded telemetry, another process
  supervisor/cache, or treating required partial analysis as successful.
- All behavior is ordinary public CLI behavior with no caller-specific mode.
