# Design

## Context

See [proposal.md](proposal.md) for motivation and [REPRODUCTION.md](REPRODUCTION.md) for the measured case. Planning identified459 project modules and186 external imports for the selected ordinary-Adam convergence theorem. Both32GiB and48GiB replay attempts resolved dependencies successfully and were terminated by the RSS supervisor during `lean_build`, before theorem identity comparison.

Read-only inspection found:

- `theorem_capsule_replay._execute_replay` invokes one `lake build <target-module>` after dependency resolution.
- `_replay_environment` allowlists only `PATH`, `HOME`, `ELAN_HOME`, `LANG`, `LC_ALL`, `TMPDIR`, plus its explicit replay/network flags. Passing an arbitrary caller environment variable is not a supported way to control the build.
- The installed replay CLI exposes timeout, RSS limit and network policy, but no build scheduling/concurrency policy. The inspected pinned Lake5/Lean4.33 help provides no build-jobs flag; do not invent `lake -j1` as a remedy.
- The receipt identifies aggregate process-tree peak and stage, but not a per-child peak breakdown. Build fan-out is therefore a hypothesis to measure, not a proved causal attribution.

The current archived replay contract already requires content validation, isolation, pinned execution, exact structural/trust comparison and classified failures. Its guarantees must remain intact. There is no synced capsule-replay spec in the current11-capability inventory; the new resource-control capability extends, rather than duplicates, that archived contract.

## Goals / Non-Goals

**Goals:** Give the replay owner an enforceable bounded-build strategy, actionable resource evidence and tests. Distinguish a fan-out problem from a single expensive compiler or dependency initialization. Preserve the same exact capsule and verification contract.

**Non-Goals:** Raising defaults again, changing theorem source or its import closure, copying project OLeans from the original checkout, bypassing content/identity checks, changing the RSS metric silently, solving the separate large-lineage JSON export issue, or claiming a mathematical failure. The initial reporting packet performed no implementation; the subsequently authorized policy is recorded below.

## Decisions

### Establish the controlling mechanism before selecting a flag

First inspect the actual process tree on a small multi-module fixture under the pinned toolchain. Select a supported implementation that demonstrably bounds expensive build work. Candidates include a genuine upstream scheduling interface, if discovered and verified, or an explicitly ordered project-module build strategy inside the fresh replay root. A guessed environment variable or advertised-but-unenforced jobs count is unacceptable.

The public API should express the selected policy explicitly. The exact flag spelling is deliberately left to the Ladon owner; `--build-jobs` is a possible interface, not an existing command. Unsupported combinations must fail clearly before expensive target execution.

### Reuse the current replay pipeline

Place policy selection in the CLI/service boundary and bounded execution in the existing replay owner. Reuse supervision, safe command/output handling, cancellation, locked dependency resolution and post-build helper comparisons. Avoid a second replay implementation or weakening the capsule's source validation. If a sequential strategy introduces multiple subprocesses, they must share one finite build-stage deadline. Dependency resolution, the complete build stage, and the final helper retain their separate existing stage budgets; do not multiply the build budget by module count.

### Keep resource measurements honest

Retain the established process-tree RSS bound and label its aggregation. Summed RSS can count shared pages more than once; it is not a measurement of unique physical memory. If adding PSS or another metric, report it separately and version its interpretation. Do not make the existing regression pass by relabelling or disabling the configured cap. Record bounded command roles, maximum observed compiler fan-out and useful child/stage peaks without exposing secrets.

## Risks / Trade-offs

- **Concurrency may not be the dominant cause** → Before a full run, use one small fan-out fixture and bounded child-process sampling to distinguish fan-out, single-process cost and setup. Stop a proposed mechanism if it cannot demonstrate its promised limit.
- **Serialized builds may take longer** → Specify finite overall/stage timeout semantics; report timeout separately from memory exhaustion. Do not reset the attempt deadline indefinitely.
- **A workaround can defeat isolation** → Retain the renamed-original-checkout regression and reject project-cache/path injection.
- **An ordinary successful build may never reach comparison** → Verification still requires the existing theorem/dependency/trust helper and all comparisons.
- **The expensive example is not a portable unit test** → Use small deterministic fixtures for policy/cleanup tests; keep the459-module reproducer as a separately authorized integration case.

The first feasibility gate is one small fixture run with the narrowest supported policy, a stated finite RSS/time budget, and an observed expensive-process concurrency bound. Only after that gate passes should the real capsule be retried. If the strategy is unavailable under the pinned toolchain, produce a classified unsupported result and concrete adapter gap rather than silently ignoring the request.

## Migration Plan

Preserve existing replay behavior unless a new policy is explicitly selected, or document a separately justified default change. Add versioned receipt fields without reinterpreting historical receipts. Update CLI help, examples and error messages alongside tests. Rollback is removal of the new policy path while retaining the existing verifier and all historical failure evidence.

The scheduling mechanism is selected by the bounded feasibility gate above; its implementation may vary without changing the external requirements or stage-budget semantics.

## Selected implementation after the feasibility gate

The user subsequently authorized implementation. The pinned 4.33 experiment
confirmed three simultaneous compilers on the small fixture (4.50 GiB aggregate
RSS), versus one with ordered module requests (1.62 GiB). The first frontier of
the actual capsule reproduced the fan-out; its three selected modules all built
individually under the same 6 GiB ceiling. Raw measurements and scripts are in
[evidence/implementation/hypothesis-check/REPORT.md](evidence/implementation/hypothesis-check/REPORT.md).

The explicit public policy is `--build-policy ordered`; `lake-default` preserves
existing scheduling. Ordered execution validates a dependency-first module DAG,
then runs `lake --no-build build +Module:deps` before each exact
`lake build +Module:leanArts`. The preflight fails closed with unsupported-facet
when imports need rebuilding or the toolchain lacks the needed facet. It never
falls back to a parallel rebuild. One deadline covers all preflights and module
compilations. Separate dependency resolution and helper stages keep their prior
budgets. Supported graph bounds are 4,096 modules and 262,144 import edges.

Optional request-local process observations retain constant-space summaries:
observed Lean fan-out, individual Lean peak RSS and descendant counts, with
explicit unavailable/partial states. Receipt additions carry their own version 1;
historical replay receipts are not rewritten. Aggregate process-tree RSS retains
its prior interpretation. No PSS-based cap substitution was made.

One public ordered replay of the actual capsule, capped at 6 GiB and 180 seconds
per stage, kept one compiler active but hit the memory limit in
`Mf.DP.GaussianPrivacyLoss` (6.09 GiB aggregate RSS). It did not reach comparison.
This exposes the next individual-module cost and is not a verified replay. See
[evidence/implementation/REPORT.md](evidence/implementation/REPORT.md).
