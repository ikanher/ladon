# Conditional provider replay and premise audit

All five exported premise-provider closures and the selected application now
complete through the public source-goal capture/completion API, including
independent source-context replay and axiom checking. This is an informed
development result. **No new mathematical error, full prose–Lean correspondence,
or fresh discovery is established.**

An actual replay exposed and led to a narrowly tested
[completion printer repair](../../../ladon-scoped-slice-traversal/evidence/completion-roundtrip/REPORT.md).
The original first success and second rejection (`Unknown identifier inst`)
remain in `replay-1/`, `replay-2/` and their command receipts. All final attempts
are separate under `repaired/`. Extraction was repeated with the final helper;
all six closed types and proof texts match the previous extraction exactly.
Fresh local observation IDs and helper identity are allowed to differ. The
original slice and its frontier labels are not rewritten.

## What was checked

Each generated goal copies the complete original source, followed by the exact
exported closed target. The submitted term is the exact exported closed proof.
Capture checks the goal twice; completion recaptures it, checks the application,
and independently compiles/replays its source environment. Each case has six
successful supervised Lean process receipts and zero residual goals. The only
observed axioms are `propext`, `Classical.choice`, and `Quot.sound`.

| Argument occurrence / application | Result | Whole command | Peak process-tree RSS |
|---|---|---|---|
| 1 | completed | 88.84 s | 5.12 GiB |
| 2 | completed | 86.22 s | 5.12 GiB |
| 5 | completed | 84.17 s | 5.11 GiB |
| 6 | completed | 83.07 s | 5.11 GiB |
| 7 | completed | 83.01 s | 5.11 GiB |
| application | completed | 83.19 s | 5.11 GiB |

Total final replay-command time is **508.49 seconds**;
maximum RSS is **5.12 GiB**, below the unchanged 12 GiB
cap. [Verification](VERIFICATION.json) checks exact submitted bytes, source
prefixes, statuses, identities, residuals, trust, process receipts and all
2,670 original primary files. This supplement consists
of public source-goal results; it is **not** a native correspondence receipt and
does not change the slice's provider-frontier states.

## What the premises mean

All 14 original local declarations remain quantified in every closure. In
particular, replaying a provider proves the relevant implication while retaining
its antecedents; it does not establish those antecedents from the exposition.

| Occurrence | Supplied provider | Remaining source interpretation |
|---|---|---|
| 1 | `slice_smooth hf p` | Joint smoothness supplies slice smoothness; identify the paper function with this periodic family/lift. |
| 2 | `hp p` | Slice periodicity is supplied; its torus/lift interpretation is separate. |
| 5 | `hzero` | The order-zero bound is an input, to be related to the chosen paper norm. |
| 6 | `hfirst`, transported by addition associativity | The pure x derivative bound at `r+5` is an input. |
| 7 | `hsecond`, transported by addition associativity | The corresponding swapped-coordinate bound at `r+5` is an input. |

Here `r = w.length`. The extracted application calls
`coefficient_seminorm_bound` at `r+1`; that theorem requests coordinate bounds
four orders above its index, hence `(r+1)+4 = r+5`. Smoothness and compactness can
give some finite bound for each fixed function and order. That does not give a
universal multiple of the paper's `C^(r+4)` norm.

The [paper, Lemma 8.6 / equation 8.19](../../../ladon-proof-correspondence-audit-umbrella/evidence/r70/sources/navier/pages-95-96.txt)
states four-derivative loss. Its proof describes a summable exponent −3 in two
dimensions; the selected formal route uses exponent −4. **The stronger input
requirements of this Lean route do not refute the paper's estimate.** A checked
full-norm interpretation, constants independent of the input function, operator
normalization, and any sharper formal route remain unestablished. The earlier
high-frequency calculation concerns a direct premise transfer, is not
Lean-formalized, and is not a counterexample to the inverse estimate.

Mean zero is a separate equation-solving condition. The selected estimate need
not require it; the source's `inverse_solves` theorem explicitly does. This
omission from the bound is not itself a defect. The estimate alone also does not
certify the paper's existence/uniqueness package.

[The premise map](PREMISE-MAP.json) is an explicitly human-reviewed local map,
not a native contract artifact. Independent review #1523 and root reconciliation
#1524 are retained in [REVIEW.jsonl](REVIEW.jsonl); the root corrected the
review's tendency to call mean-zero absence a defect and separated existence
of some bound from the required uniform norm bound.

## Scope and next obligation

The useful remaining obligation is a source-bound comparison between the
paper's full fourth-extra-order norm and a formal route to the displayed
estimate. Repeating these conditional closures cannot supply that comparison.
The known richer statement remains outside the current formal-contract producer;
no binder-cap increase, synthetic norm substitution or new producer is credited.
Parent tasks 2.1, 3.2, 3.3 and 3.4 stay open. Caching remains deferred and nothing
was pushed. The repair report records the stopped quality-script full-suite
incident separately; it contributes no qualification result.
