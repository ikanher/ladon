# Lean extraction runtime

Ladon's `lean` extraction backend loads target Lean environments. Imported
initializers may execute, so this backend is not safe analysis of an untrusted
repository. The default `text` backend does not start Lean or Lake.

The ordinary `ladon` command controls the runtime:

- `--lean-extraction-scope root|inventory` selects one root or the discovered
  inventory.
- `--lean-batch-size N` sets the ordered inventory batch size and rejects
  values below two.
- `--lean-timeout SECONDS` sets a finite deadline for each helper batch.
- `--lean-cache-dir PATH` enables the versioned strong cache.
- `--lean-strict` turns any partial helper batch into a required-phase failure
  without discarding successful rows or diagnostics.

The default batch size is 8. This amortizes Lean environment startup for normal
inventories while bounding retained parser/environment state and limiting how
many modules must be retried after one process-level failure. The downstream
benchmark packet may tune this value; the runtime contract does not depend on
the exact default.

Each helper runs in its own process group with a 120-second default deadline.
Timeout, cancellation, malformed protocol, and parent errors terminate and reap
the full group. The helper emits versioned NDJSON module frames followed by a
terminal summary. Module failures are structured rows, so a later failure
cannot erase an earlier validated result.

Cache entries live under `ladon-lean-cache-v2`. A fingerprint includes protocol
and helper identity, extraction options, resolved Lean and toolchain state,
Lake configuration/manifest state, the target source, its resolved transitive
local import closure, and identifiable compiled state. When compiled state
cannot be fingerprinted, Ladon reports a cache bypass instead of a sound hit.

Lake-declared library roots and `srcDir` values are resolved before the
repository-relative fallback. Multiple libraries and declared generated roots
are supported. Fallback, malformed configuration, absent roots, and ambiguous
module ownership are visible in extraction diagnostics.

Extraction never invokes `lake build`. `--build` is the sole build opt-in owned
by the shared CLI phase; the extraction report records both whether it was
requested and that extraction itself did not invoke it.
