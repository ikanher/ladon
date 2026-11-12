# Independent audit of v3 pending-family profiles

Date: 2026-11-12

Scope: read-only inspection of the accepted v3 registration, selected corpus
sources, source-goal CLI, and Lean helper. This is a profile-contract audit; it
does not execute a scored baseline case or revise any accepted result.

## Finding

Registration v3 is insufficient to qualify either pending
`source-goal-probe-v1` family. A representative execution with values chosen
for `<line>` and `<column>` would be an unregistered harness, not valid batch
qualification. The registered templates retain both placeholders and include
no per-case plans or overrides.

The capture CLI requires an exact source position, and the Lean helper extracts
goals from `TacticInfo` there. It does not query the type or value of a selected
declaration. The four `existence-defaults` subjects and
`operation-semantics` cases 01–02 are proposition-valued definitions, so
capturing a position in those definitions cannot observe a proof goal of the
represented proposition. Operation cases 03–04 are theorems with `by` blocks,
but v3 does not bind the capture position, goal identity, or local context.

The registered completion operation only tries to prove the one captured
positive goal. A failed completion is unresolved under the rubric; it does not
provide a checked counterexample for a false claim. No per-case proposition
polarity or counterexample-check protocol is frozen by v3.

## Required correction

Before either family runs, create and independently review a versioned
registration correction that binds exact per-case propositions and query
plans, exact generated source bytes/digests and selector positions, imports,
candidate tactic and runtime. The query adapter must target the selected
definition's proposition, not its declaration type `Prop`. A fault judgment
must be supported by a checked negation or another explicitly registered
counterexample check; inability to prove either polarity remains unresolved.
Keep the accepted v3 file and prior batch records immutable. The adapter
feasibility probe itself is not a scored case.

## Source references

- `common-registration-v3.json`: pending family templates and unresolved
  placeholder positions.
- `corpus/mathlib/ExistenceCases/Case01.lean` through `Case04.lean`:
  proposition-valued `def subject` declarations.
- `corpus/lean/CoreCases/operation_semantics_01.lean` and
  `operation_semantics_02.lean`: proposition-valued `def subject` declarations.
- `corpus/lean/CoreCases/operation_semantics_03.lean` and
  `operation_semantics_04.lean`: theorem proof blocks without registered
  selectors.
- `src/ladon/proof_search_goal_cli.py`: exact line/column capture arguments.
- `src/ladon/lean/ladon_source_goal_helper.lean`: goal lookup from tactic info
  at the requested position.
- `src/ladon/source_goal_completion.py`: completion consumes the captured goal
  and submitted proof term.

Conclusion: do not execute or score either pending family under v3. The v3
configuration-freeze acceptance and already accepted feasibility and
premise-provenance batches are unaffected.
