# Adam energy follow-up: complete chain, native heartbeat limitation

The full displayed statement was proved with the pinned Lean compiler:

`J_T ≤ 63 (73/10)^2/T + 1011 (26/T + 1/999) ∧ RHS ≤ 29/10`.

The [exact theorem](direct/CheckedEnergyChainDefault.lean) preserves the real formal
owner's telescope and uses the actual-model energy producer, `logEnergyBound_envelope`
and explicit numerical arithmetic. It assumes neither energy inequality. The root
reconstructed this formal conjunction from the printed source chain; its assumptions
and object mapping are the inspected interpretation from r01, not a certified TeX parser.

## Checked evidence

- [Default compiler result](direct/result-default.json): exit zero, 3.531 seconds,
  sampled supervised-tree RSS peak 7,054,340,096 bytes (~6.57 GiB), no timeout/memory stop.
- [Compiler result with 800,000 heartbeats](direct/result.json): exit zero, 3.532 seconds,
  sampled RSS peak 7,063,384,064 bytes (~6.58 GiB).
- Both `#print axioms` outputs contain only `propext`, `Classical.choice`, `Quot.sound`.
  The direct default check establishes that the larger compiler heartbeat setting
  was unnecessary for this standalone theorem.
- Both checks used the pinned Lean 4.33.0 binary, existing compiled libraries, a
  180-second wall limit, 8 MiB output limit and 12 GiB RSS cap. No Lake build,
  dependency repair or target source edit was performed.

This closes the intermediate-inequality evidence gap as **ordinary Lean evidence**.
The terminal ceiling's native application/replay/trust success remains r01 evidence.
No mathematical source fault was established, and neither result establishes a general
natural-language interpretation or detection advantage.

## Reproducible native limitation

Three native completion attempts against the previously captured real ceiling goal
failed as `application-process-failed`, with deterministic heartbeat exhaustion:

| Attempt | Submitted proof | Operation seconds | Peak sampled bytes | Diagnostic stage label |
| --- | --- | ---: | ---: | --- |
| 01 | Explicit conjunction, then transitivity | 44.862 | 9,543,389,184 | elaborator, 200000 heartbeats |
| 02 | Same conjunction with term-local `set_option maxHeartbeats 800000 in` | 44.202 | 9,543,995,392 | isDefEq, 200000 heartbeats |
| 03 | Separate named intermediate inequalities, then transitivity | 45.082 | 9,540,136,960 | isDefEq, 200000 heartbeats |

All wall and memory bounds remained fixed. No failed run is a native proof acceptance.
The first two attempts explicitly contain the same full conjunction; the third uses
the two checked steps separately. The standalone theorem directly asserts the conjunction.
No general performance ratio is inferred from these different execution routes.

The root inspected `ladon_source_goal_completion_helper.lean`. It elaborates the supplied
term, closes it, prints/reparses it and compares expressions in several surrounding
contexts. The submitted term-local option does not cover all these contexts. The retained
message identifies heartbeat exhaustion but does **not** isolate the exact internal
phase; `isDefEq` occurs in multiple places. It is not yet established which context or
heartbeat-accounting boundary caused the failure, nor that a larger global budget alone
would make native replay pass. No production fix was attempted without that diagnosis.

## Next useful product work

Reproduce this failure with phase-level heartbeat observations in an isolated helper
experiment. Determine whether the budget is consumed during candidate elaboration,
closure, explicit re-elaboration or equality checking. Then qualify a finite, explicit
resource control for the affected checking stages through the existing completion route,
if that is the remedy. Preserve replay/trust checks and stale-context protection; never
accept the term solely because ordinary Lean compiled it. This is a concrete consumer
blocker, not authorization to resume broad semantic-diagnostic integration.

## Custody and scope

[CUSTODY.json](CUSTODY.json) hashes source inputs, all retained local artifacts, and the
original raw capture. Raw capture remains in the r01 local experiment directory. This
follow-up retains exact command scripts, stdout/stderr, native failures and direct Lean
source/results. It does not bundle the compiled dependency closure needed for independent
replication. The r01 reports remain unchanged. No independent human review was performed.
