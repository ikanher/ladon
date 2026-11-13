# synthetic-comparison-r01 process-bound feasibility

## Finding

There is no existing Ladon bound for the number of Lean executables started. `run_bounded_target_process` bounds one direct child’s wall time, output and optional RSS, and signals/reaps that child’s process group on stop. It does not count descendant Lean execs or impose a launch quota. Resource observation is not an execution counter.

Relevant launch shapes include direct absolute Lean commands from `prepare_direct_lean_execution`, where the verified `LeanToolchainContext.lean_path` is used and `PATH` is set to the toolchain’s bin directory, and Lake commands such as `lake build` / `lake env lean`. Lake can start Lean while remaining inside Ladon’s supervised process group. A Python helper or a Lake child can also start Lean independently of the original Ladon child. Toolchain resolution itself runs bounded `lake --version` and `lean --version` commands.

## Smallest experiment-only route

Use the already-probed bwrap boundary to expose a counting wrapper at the *resolved pinned Lean executable pathname* inside each arm’s sandbox, and expose the real pinned executable at a separate private pathname (for example, `/run/lean-real`). Bind-mount the original toolchain tree read-only as needed for shared libraries and Lake, then overlay only the pinned Lean pathname with the wrapper. Make the wrapper atomically reserve a start in an arm-scoped SQLite database (`BEGIN IMMEDIATE`, bounded busy timeout, fail closed on DB/lock errors), reject start 21, and `execve` the alternate real binary with unchanged argv/environment. This counts an attempted launch before the real Lean image begins and counts concurrent starts correctly; a shared database serializes racing wrappers. Keep a single counter over the full arm, including setup/version probes if those are part of the registered arm. If the stated ceiling means 20 total across *both* arms, use a shared global quota as well as per-arm attribution.

The pathname overlay is compatible with the normal routes found in source: Ladon uses the resolved absolute `lean_path` for direct invocations and puts that executable’s parent first in sanitized `PATH`, which Lake’s `lean` lookup should inherit. The toolchain resolver resolves symlinks before recording the selected path, so install the overlay at that canonical path, not just at the Elan shim name. Keep Lake itself available, but treat `lake build` and `lake env lean` as indirect routes that must hit the same overlay.

## Gate/caveats

This is robust only if the arm is procedurally restricted to the registered pinned toolchain and cannot reach an uninstrumented Lean copy. In the sandbox, remove/hide alternate toolchain binaries and Elan shims (or prove via an exec trace that all Lean execs resolve to the overlay); do not leave `/run/lean-real` reachable through PATH or an alternate command route. Also prevent the target from modifying/replacing the wrapper, counter DB, or mounts. Keep the DB outside writable target roots. The supplied bwrap/strace success is useful feasibility evidence, but this review did not run either probe.

A pathname wrapper alone cannot police arbitrary commands that copy Lean elsewhere or invoke an alternate installed version. The exact unresolved gate is therefore the arm’s executable-scope rule: either restrict and document the arm to the one pinned toolchain and verify with strace that every Lean exec crosses the wrapper, or require an OS-level execution policy that blocks all other Lean binaries. Do not claim a general host-wide quota from the wrapper alone.

No production edits, tests, cases, or audit runs were made.
