## Context

The live Lean-backed owner run returned a partial report and exit 1 without
naming the controlling failure. Long text runs also produced no progress. This
child makes existing phases observable and bounded without creating another
process supervisor or helper protocol.

## Decisions

### Progress is diagnostic-only

`auto`, `plain`, `json`, and `off` modes write only to stderr. `auto` emits
periodic output only for an interactive stderr. Events use one versioned shape
and are rate-limited by five seconds or 100 completed modules.

### Overall limits are cooperative plus supervised

Overall wall time, process-tree RSS, and report bytes supplement existing
per-build and per-helper deadlines. In-process phases check a shared budget at
deterministic boundaries; external children remain owned by the existing
process-group supervisor.

### Partial state has one controlling diagnostic

Every incomplete phase has a stable failure class, non-empty reason,
completed/omitted counts, cache outcome, and bounded diagnostics. Exit 1 always
emits one Ladon-authored stderr summary and names a written partial report.
Incomplete populations suppress or label metrics that would otherwise look
complete.

### Migrate strictness through the existing selector

`--lean-strict` remains a two-minor compatibility alias for
`--fail-on phase:lean_extraction:partial` and emits a deprecation diagnostic.
It never becomes a semantic no-op.

## Existing Owners And Exclusions

`ladon-cli-execution-contract`, `ladon-report-contract-v2`, and
`ladon-lean-extraction-runtime-hardening` retain exit, envelope, supervision,
batching, cancellation, and cache authority. This child adds no wrapper
process, helper protocol, or alternate cache.

## Risks

Progress can corrupt machine output unless channel isolation is tested.
Resource enforcement differs by platform, so unsupported enforcement is
reported rather than claimed. Cancellation preserves only atomically validated
evidence.
