# Task 2.2 source-aware check route scout

## Recommendation

Use the existing exact source-goal completion pipeline for the final kernel
implication, with an outer connection supervisor modeled on
`real_bound_native_transfer.py` / `real_bound_native_check.py`. Do not make
same-file or byte-prefix status itself an owner proof. A viable first gate is
two immutable, independently revalidated owner inputs plus one generated
connection context whose imported-owner closure is checked against both
observations; if that closure cannot be constructed inside the pinned context,
return `unresolved: source-context-unavailable`.

The final Lean goal should be generated from the retained typed propositions,
not caller-supplied text: `Pformal → Pauthored` for an unconditional route, or
`Pformal → (H₁ → … → Pauthored)` for every explicit bridge/premise in its
recorded order. Terms for specialization, norm/carrier conversion, aliases and
coefficient changes must each have a separate exact typed goal and checked
term; the final implication must still mention their results as hypotheses.
Do not build the source theorem or authored definition from a theorem name
alone. Select the formal declaration's *type* and the authored declaration's
*value*, record both complete Expr values/types and their declaration owners,
and have Lean re-elaborate those owners in the selected context.

## Existing API seams

- `src/ladon/correspondence_check.py::_check_goal(goal, term, root, source,
  symbols, toolchain, prepared=None)` is the smallest direct proposition
  checker. It copies exact source bytes into a private `LadonCorrespondence`
  file, typechecks the generated target, captures it, and delegates to
  `complete_source_goal`. It returns typed-subject/capture/completion/replay
  evidence. The completion API is stronger as a reusable boundary:
  `SourceGoalCompletionRequest(repo_root, capture, term, toolchain,
  timeout_seconds, max_output_bytes, max_rss_bytes)`;
  `complete_source_goal` re-captures the goal, checks the term, writes and
  compiles a private replay module, checks source/helper/toolchain/import
  custody, and records axiom coverage. This should be the final implication
  gate, not a syntax comparison or a Python relation result.
- Fresh formal admission is already structured as
  `real_bound_native_production._verify_production` → `_current_source` →
  `replay_real_bound` / `check_real_bound`; `_fresh` in
  `real_bound_native_analysis.py` verifies admission goal coverage and exact
  typed record presence. Preserve `real_bound_native_analysis_bundle.py::_semantic_owner`
  comparison after replay: it prevents a fresh result from silently replacing
  the saved request, source text, environment, subject/source-map refs or
  record. Formal saved receipts alone have no fresh authority.
- Authored freshness is `real_prose_native_production.validate_production`
  followed by `replay_real_prose_bound`; the native worker rebuilds the exact
  observation and recognizer from original interpretation/context, then
  `inspect_real_prose_bound` reports history as `freshCheck: false` and
  `evidenceAuthentication: not-established`. Keep that distinction in the
  connection history too. The authored record contains the proposition value
  inside its recognition observation; its native owner is the exact
  interpretation/source-map/context plus observation, not the display name.
- `real_bound_native_transfer.py::_transfer_run` already establishes the
  orchestration pattern: one monotonic deadline, `_remaining(deadline)`
  before each stage, fresh admissions, semantic-owner equality, selected-route
  residuals, then a private worker request containing `deadlineMonotonic` and
  all three policy caps. `real_bound_native_transfer_check.py` uses
  `_execute_job` and a parent-owned `TemporaryDirectory`; its worker rechecks
  owners and reserved helpers, calls `_check_goal`, and re-verifies sources
  and checker identity before returning. Connection can reuse this shape, but
  should not reuse its same-context two-contract semantics as proof of the
  authored/formal owner relation.

## Context custody challenge

The candidate same-file/prefix rule is insufficient on its own. The actual
formal owner is in a separate Mathlib 4.34.0-rc2 project
(`/home/codex/projects/navier-stokes-retest-4/formalization`, e.g. the
`NavierStokes.SmoothFamilyTorusInverse` module); the authored native reading is
currently produced in Ladon's isolated `ProseCases` source context under
`openspec/changes/ladon-real-prose-contracts/evidence/authored-real-native-20261027/runtime/`.
Their roots, direct import closures, source modules and compiled inventories
are not currently one custody domain. A copied declaration name, matching
module string, or appending authored text to formal source does not prove
which owner supplied a constant. An appended file can shadow names or change
namespace/notation/scoped instances; an import can resolve another compiled
module. Capture both source byte digests, selected declaration span/name,
normalized and original full typed proposition, environment/toolchain identity,
direct compiled-import inventory and module-file hashes. Then either:

1. prove an exact generated composite-source closure that re-elaborates both
   owner expressions and captures the final goal under that closure; or
2. preserve independent owner checks and make the imported-source bridge an
   explicit unresolved obligation.

The current `_check_goal` observes copied original source even in prepared
mode because imports do not export every local elaboration extension. This
helps exact local checking but does not automatically combine two separately
rooted environments. `prepare_direct_lean_execution` and source-goal capture
inventories are the relevant context/environment seams. A strict prefix check
can be one byte-ownership condition only after both module/import closures are
shown equal; it cannot establish semantic owner identity.

## Deadline, temporary directory and size seams

- `complete_source_goal` invokes `capture_source_goal`, an application process,
  and an independent replay. Its request has a single `timeout_seconds`, but
  each `_run` supplies that same duration to the runner. A caller passing
  `deadline - now` does not itself make those nested calls share one absolute
  clock. Wrap the complete connection worker in `_execute_job` with one
  parent-owned temporary workspace and deadline; thread remaining time through
  nested calls, or ensure all subprocesses are descendants governed by that
  outer supervisor. The final source/custody checks must happen before the
  outer deadline closes. `_check_goal` also has a hardcoded 60s typecheck,
  8 MiB output and default RSS cap; it has no `deadlineMonotonic` parameter.
- `complete_source_goal` owns its own `TemporaryDirectory` for source snapshot,
  helper, generated replay source and compiled source-context module. An outer
  worker kill cleans this inner directory under normal context-manager exit,
  but parent-killed descendants/files require the caller-owned outer temp
  directory pattern (as in transfer) to make lifecycle auditable. Recheck
  original source, helper bytes, runtime/toolchain and inventory after final
  completion.
- The existing observation artifact is about 3.31 MB and authored production
  history is about 5.75 MB (`.../live/navier-observed-final.json` and
  `.../live/navier-produced.json`); together they exceed the unchanged 8 MiB
  protocol limit before adding formal history, bridge terms, receipts or result.
  `_planned_input_size` and worker protocols reject oversize payloads; do not
  pass both entire JSON histories in one worker stdin. First cheaply measure
  canonical connection request and worst-case retained result. Use bounded,
  exact history references/owner digests with separately validated artifacts
  only if the contract's full-history requirement remains met; otherwise emit
  `unavailable: history-exceeds-8MiB`. No truncation, compression, dropping
  receipts, or global cap change.

## Informed pair feasibility and cheapest falsifiable gate

The authored artifact is an observed proposition value, not a theorem. The
formal source's relevant admitted result has a five-order input; the frozen
authored reading uses four. Existing `.codex/state/navier-pair-integration/BRIDGE-RESULT.json`
shows the exact selected four-order application rejected because Lean expects
`shiftFour n` where the declaration requires `n + 5`. It also records a
five-order control accepted. Thus that chosen route must remain rejected or
unresolved, never “false”; adding an unproved four-to-five bridge premise
would only state a conditional result and must be visibly retained. The
coordinate-norm bridge is separate and must retain its actual
order-dependent coefficient.

Cheapest falsifiable gate before API freeze: with no new production code,
construct a compact, owner-bound pair from the saved formal production and
authored production, replay each independently under one outer 600s/12GiB/
8MiB supervisor, then try to generate and capture one exact typed final goal
under a shared imported context. Include all required bridges/premises as
explicit hypotheses. The gate passes only if (a) both replays preserve the
same semantic owners, (b) the composite context inventory binds both sources
without name-only resolution, (c) the captured target structurally equals
exactly `formal TYPE → ordered typed premises → authored VALUE`, (d) the
kernel completion succeeds, and (e) complete history/request/result fit the
8 MiB cap without resetting time. Expected informed selected-route outcome is
an unresolved/rejected five-vs-four obligation. A generic unrelated positive
pair should establish that the checker can accept a real connection; one
actual Mathlib unrelated global/set control is enough for this route probe.

This is feasibility advice only. I ran no tests, Lean, build, or production
checks and claim no connection proof.
