## Why

Inventory extraction currently starts one unbounded Lean process per file,
making cold runs slow, memory-heavy, and vulnerable to orphaned processes.
Cache hits are fast, but invalidation does not account for enough of the target
toolchain and imported environment to be trusted.

## What Changes

- Replace per-file inventory subprocesses with a bounded batch extraction
  protocol that amortizes environment startup.
- Add configurable deadlines, cancellation, subprocess-group cleanup, and
  structured partial-failure rows so one module cannot strand an analysis.
- Include Lean/toolchain identity, Lake configuration, helper identity, target
  source, and imported environment fingerprints in cache validity.
- Discover Lean module roots from Lake libraries, including `srcDir`, multiple
  libraries, and declared generated roots, while retaining a documented
  fallback for simple repositories.
- Record extraction provenance, cache status, elapsed time, and bounded resource
  counters in the ordinary report contract.
- Document that Lean-backed extraction loads target environments and is not a
  safe operation for untrusted repositories.
- Preserve the CLI contract that target builds are opt-in and never silently
  triggered by extraction.

## Capabilities

### New Capabilities

- `ladon-lean-extraction-runtime`: Bounded, cache-correct, Lake-aware Lean
  extraction lifecycle and failure behavior.

### Modified Capabilities

None.

## Impact

- Affected code: Lean helper protocol, `lean_extraction.py`, module discovery,
  subprocess management, cache layout, pipeline phase records, and CLI options.
- Affected tests: fake-process lifecycle tests, real-Lean batch integration,
  cache invalidation cases, multi-library Lake fixtures, timeout cleanup, and
  partial-result behavior.
- Cache formats may be versioned or invalidated once when the stronger contract
  lands.
