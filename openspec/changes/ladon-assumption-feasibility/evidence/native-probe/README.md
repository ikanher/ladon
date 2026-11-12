# Native mathematical feasibility experiment

The bounded experiment passed, including independent reproduction. It constructs
the previously missing mathematical question from a real Lean declaration's
typed telescope, then uses existing Ladon capture, completion and independent
replay to check a supplied witness or refutation.

| Selected assumptions | Generated question | Checked outcome |
| --- | --- | --- |
| `n : Nat`, `n = 0` | `∃ n : Nat, n = 0` | Witness accepted |
| `n : Nat`, `n = 0`, `n = 1` | `∃ n : Nat, n = 0 ∧ n = 1` | Refutation accepted |
| Fixed literal `1 = 0` | `(1 : Nat) = 0` | Refutation accepted |
| Witness attempts to use absent `h0` | Same contradictory context | Rejected |
| Witness uses `sorry` | Same contradictory context | Trust rejected |

The first three proofs have accepted independent replay, complete axiom
coverage and no observed axioms. The `sorry` case reaches replay but is rejected
for `sorryAx`; replay success alone never establishes mathematical acceptance.
Lean's theorem-under-construction appears as an implementation-detail local.
There are no ordinary ambient locals; existing completion rejects dependencies
on implementation-detail locals and replays a closed proof independently.

[RESULT.json](RESULT.json) gives the concise machine-readable result.
[The final qualification](verification/qualification-r4/qualification.json)
and [completion receipts](verification/qualification-r4/completion.json) retain
commands, statuses, exact generated goals, source/environment bindings, replay
sources, axioms and resources. The final qualification took 114.63 seconds;
including the three retained prior attempts it took 172.48 seconds of supervised
execution, within the original 600-second budget. Peak observed process-tree RSS
was 3,800,809,472 bytes, about 3.54 GiB, under the 12-GiB cap.

The [independent review](verification/independent/REVIEW.md) reproduced all five
completion outcomes in a separate scratch project. Its successful completion
run took 111.90 seconds. It also reproduced the `omega` replay limitation below.

## What is checked

[Native.lean](FeasibilityProbe/Native.lean) takes an actual `Lean.Expr` obtained
from `ConstantInfo.type`. Data binders become existential variables; proof
binders contribute their proposition types as conjuncts. It does not reconstruct
types from displayed strings. The declaration's conclusion is deliberately
excluded from this separate **premise feasibility** question.

[Acceptance.lean](Acceptance.lean) compares generated expressions with separately
elaborated expected propositions using definitional equality and rejects open
results. It also verifies the original conditional theorem types separately.
In particular, the valid theorem deriving `n = 37` from contradictory hypotheses
is preserved. An impossible context is not automatically an exposition error.

Proof-dependent data domains are explicitly unsupported. Additional
[closure guards](ClosureGuards.lean) reject a `let` hiding subsequent binders and
a declaration returning data rather than a proposition. These cases first failed
against the proposed implementation, then passed after conservative rejection
was added. Frozen test hashes remained unchanged. Historical red scaffolds and
failure receipts are retained under `verification/`.

## Limits and next mathematical work

This is an isolated declaration-telescope prototype, not a production stage or
an automatic discovery result. The initial data profile admits Nat, Int and Rat;
the executed mathematical examples use Nat. The fixed-literal case does not test
a parameter-assignment API. Capturing the complete context at an actual proof
position, transitive local-value aliases, assignment binding, operational proof
search and the full matched evaluation remain unfinished. No source-fault
judgment or completed OpenSpec capability is claimed.

The next mathematical step is to apply the same independent closure to the
actual selected proof context, with tests ensuring every hypothesis, fixed
assignment and proof-derived value is retained or explicitly unsupported.

One existing completion limitation surfaced: a supplied `omega` refutation
applies, but its independent replay fails on a missing generated `_proof_1`
declaration. [The failed candidate](verification/qualification-r3/completion.json)
is retained and receives no inconsistency authority. The final run uses a direct
equality proof of the **same** refutation. This establishes supplied-term
validation only; it does not establish that an automated tactic route succeeds.

## Reproduce

From the Ladon checkout, with Lean 4.32.1 already installed:

```bash
PYTHONPATH=src .venv/bin/python openspec/changes/ladon-assumption-feasibility/evidence/native-probe/qualify.py --output-directory /tmp/ladon-feasibility-check
```

Use a new output directory outside the input project. The runner compiles the
helper and fixtures, then runs existing Ladon completion with one decreasing
600-second deadline, a 12-GiB process-tree RSS cap and bounded command output.
The adjacent `Witness`, `Refutation`, `Fixed`, `Leak` and `Sorry` files are
intentionally unfinished source-goal capture inputs; their proofs are supplied
through the checker, not written into those inputs.
