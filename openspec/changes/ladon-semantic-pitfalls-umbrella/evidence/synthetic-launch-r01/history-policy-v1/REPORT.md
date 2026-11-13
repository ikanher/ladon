# Launch preparation r01

The registered inputs and frozen cases match their recorded hashes. The prior
stale-checksum diagnosis was incorrect: `sha256sum -c` was invoked from the
repository root while its entries were relative to the packet directory. Running
it in the packet directory passes every entry. No checksum was regenerated and
no registered input was changed to obtain this result.

The local runtime's actual source bytes, dirty state, Python dependencies and
pinned Lean/Lake binaries are recorded in RUNTIME.json. Reverify that record at
launch; a saved runtime record does not prohibit later checkout changes.

A new common original-capsule project was prepared outside the repository at
`/home/codex/projects/ladon-evaluations/synthetic-r01/prepared`. It reuses only
pinned external package/cache material from the previous local acquisition.
Original project sources and metadata match the retained capsule, and its five
project modules were freshly rebuilt. SETUP.json distinguishes that reuse from
original project rebuilding. No donor or development symlink dependency or
exposed project helper was found.

The measured common build completed in 12.69 seconds with sampled peak process
tree RSS 6,553,047,040 bytes (about 6.10 GiB), under the 12 GiB bound. The retained
raw outputs and common-build.json are authoritative. Dependency-copy time and
memory were not measured; complete setup costs remain unavailable.

## Remaining launch gate

The host supports bwrap filesystem isolation and strace process tracing. The
independent PROCESS-GATE-REVIEW.md confirms that the existing Ladon supervisor
bounds process-tree time, RSS and output but does not enforce the registered
lifetime count of twenty Lean starts. Sampling process names cannot establish
that count. An ordinary CLI-call counter also misses Lake/Ladon child processes.

Before launch, qualify an experiment-only gate for the canonical pinned Lean
executable with an atomic shared counter, and verify direct, Lake and Ladon
paths, concurrent reservations, rejection of start 21, and process cleanup.
Declare the procedural restriction to that pinned executable and record any
bypass exposure; a pathname wrapper alone is not a host-wide execution policy.
The registration's count requirement has not been weakened. No mathematical
audit context may start while this gate is unqualified.

This is launch preparation evidence, not a mathematical audit result. No auditor
has read a case and no comparison score or detection claim exists.

## Workspace staging

The physical-copy batch was deliberately stopped while the Lean-count gate was
unqualified. Two unit-01 workspaces have copied prompts; unit-02/control is a
partial project copy. All staged paths are unlaunched and must be verified before
use. CURRENT.json records their state. No ten-workspace readiness is claimed.
