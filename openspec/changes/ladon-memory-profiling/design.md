## Context

Python 3.11–3.12; core has no third-party runtime dependencies. Installed probes find
psutil 7.2.2 and Memray 1.20.0. Existing supervision samples /proc RSS and counts
children. The owner asked whether a new module was needed: it is not necessary to
start measuring. External instrumentation will first establish the actual missing data.

## Decisions

Run a representative stored-lineage query against matrix-factorization with a temporary
psutil sampling harness. Repeat with external Memray instrumentation. Keep the harness
and raw evidence local; document public profiler commands and scope in Ladon's docs.
Preserve stdout/stderr separately and query payloads. Use finite execution bounds.
Record sampled parent/descendant RSS and PSS/USS, profiler versions, command, source
identity, time, sample count and limitations. Do not treat sampled peaks as exact or
RSS as additive physical memory. Do not infer a benchmark from one run per mode.

Memray attributes Python and native-extension allocations in its interpreter, not
separately launched Lean binaries. psutil observes process memory but cannot attribute
Lean allocations to source lines. PSS/USS readings are slower and may be inaccessible.

## Superseded draft

An initial additive CLI contract produced 4 expected failures (10 validation cases
passed for unrelated CLI rejection). No production code was written. That unimplemented
contract and red log are retained under ignored `.codex/state/memory-profiling/`.
They do not certify this documentation/measurement deliverable. No new CLI, packaging
extra, library module, caching, exact accounting or semantic-audit rerun is authorized
by this narrowed work package.

## Acceptance

1. Confirm installed APIs and run one bounded real Ladon query with process sampling.
2. Qualify actual Memray capture and report; retain costs and nonclaims.
3. Document reproducible external commands, installation/interpreter selection,
   subprocess scope, profiling overhead and remaining gaps. Validate this change.
