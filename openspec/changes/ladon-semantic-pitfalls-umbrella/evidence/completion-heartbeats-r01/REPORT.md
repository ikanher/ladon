# Native completion defaults and generated auxiliary replay

The retained Adam full-chain term now completes through the production CLI with
**default resource settings**. It has no residual goals, accepted compiler replay,
and complete transitive trust with only `Classical.choice`, `Quot.sound`, `propext`.
[DEFAULT-RESULT.json](DEFAULT-RESULT.json) retains the exact command, selected statuses,
resource observations, raw local evidence path/digest and helper identity. No heartbeat,
timeout, RSS or output-limit override was supplied.

## Cause and implementation

The [isolated phase trace](PHASE-TRACE.json) reached submitted-term elaboration, closure,
round-trip target parsing and proof re-elaboration before exhausting the old 200,000
heartbeat budget. The failure was in proof re-elaboration, before the final expression
comparison. A term-local setting did not cover the surrounding helper work. Lean's
`Core.Context` also caches its active heartbeat budget separately from its options map.

Completion now defaults to 800,000 heartbeats, configurable with `--max-heartbeats` or
`SourceGoalCompletionRequest.max_heartbeats`. The helper updates both options and the
cached work budget for the whole checking/closure/round-trip scope. Independent replay
uses the requested setting too. Source observation is unchanged: the capture's original
options and canonical freshness binding remain authoritative. Resource accounting records
the requested value. Validation rejects nonintegers, zero, negative and unsupported tick
ranges before toolchain work. Time, memory and output controls remain independent.

The budget fix exposed another real failure: a tactic-generated `_proof_1` was available
in the checking environment but absent from the exported replay context. The
[budget-only failure](BUDGET-ONLY-FAILURE.json) is retained. Export now uses the accepted
checking environment, including generated auxiliary declarations, rather than only the
original source environment. Independent replay and transitive trust remain mandatory.
A generated legitimate theorem passes; a generated axiom is replayed and trust-rejected.

## Measured end-to-end result

The operation took 94.49 seconds (97.89 seconds including CLI preparation), with sampled
supervised-tree RSS peak 9,580,187,648 bytes (~8.92 GiB), below the default 12 GiB cap.
Each supervised process stayed within the default 60-second deadline; the observed helper
execution times were approximately 6.83, 7.15, 21.48 and 22.94 seconds. The four-process
sum is not the whole operation time. These are one-off qualification measurements, not
a benchmark or an exact kernel high-water mark. No extra profiler run was needed.

The same source goal and exact term are retained from r02. The primary TeX source hash
still matches r01. No target build, target source edit, index update or dependency repair
was requested. This establishes a usable completion path, not a certified prose mapping,
whole-paper result or incremental mathematical-detection benefit.

## Verification

New test-first regressions cover CLI/API default and explicit budgets, invalid inputs,
propagation without changing the capture, replay budget, real low-budget exhaustion,
default acceptance, generated auxiliary replay and generated-axiom rejection. Existing
completion tests cover stale contexts, placeholders, self/internal dependencies, residuals,
printer bounds, local definitions and universe/instance round-trips. The full source-completion suite passed **62/62** in 217.81 seconds; its raw log
is retained. Production commit: `a8f4420`. The installed-distribution smoke passed from the worktree based on that production
commit, including the packaged Lean helper. See VERIFICATION.json and installed-smoke.log.
Two earlier selection preflights stopped before building (dirty HEAD, then untracked
required evidence); staging the intended inputs resolved the second and the worktree
check passed. These were harness selection failures, not product-test failures.

Scoped Ruff and changed-file complexity checks pass. The repository-wide strict gate
still stops on ten pre-existing real-bound complexity findings; no quality policy or
existing test expectation was weakened. No independent human-review claim is made.
The bundled guide/skill and shared Ladon source-goal reference are updated (shared commit
`200b379`). No runtime dependency, new production module or database migration was added.
