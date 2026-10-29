# Authored Real proposition feasibility

## Result

The selected source interpretation can be elaborated and observed **without
asserting it as a theorem**. Passing that exact typed proposition to the current
Real recognizer fails at its bound-predicate grammar. A wrapper around existing
interpretations alone therefore does not connect the source pair.

The current reader requires a function/set/order/bound predicate. The selected
reading has function/order/bound arguments and no set binder. It also uses named
shift and product operations; separate controls show that these aliases are
outside the current reader's direct arithmetic grammar. These are concrete
implementation gaps, not mathematical failures in the paper.

The [child design](../../design.md) uses these results to choose proposition-value
observation, a distinct global-bound profile, and explicit checked alias
normalization. Existing native interpretation artifacts supply source custody;
the design does not add another duplicate source-map format. Old Nat and
extracted Real contracts keep their meanings. Native production, admission,
connection and graph propagation remain unimplemented for this reading.

## Actual probes

All rows below use fresh Lean frontend elaboration of saved source, followed by
the unchanged `observe_bound_shape` function only when a proposition was emitted.
The helper is a scratch experiment, not a public Ladon producer.

| Input | Proposition observation | Existing Real recognizer |
|---|---|---|
| Unchanged `FourOrderReading` | Observed | Unsupported bound-predicate application |
| Unrelated set-indexed estimate, literal loss 3 | Observed | Candidate shape; predicate admission unresolved |
| Same generic estimate with shift alias | Observed | Unsupported scale |
| Same generic estimate with product alias | Observed | Unsupported Real-product shape |
| Selected non-Prop definition | Rejected | Not run; no shape output |
| Selected existing theorem | Rejected by definition-value path | Not run; no shape output |

The generic estimate is a **definition of a proposition**, not a theorem. The
negative theorem-selection case means this experimental value reader refuses
to misread a proof as a proposition; ordinary theorem observation remains valid
through Ladon's existing separate path. No axiom, `sorry`, proof placeholder,
new proof or paper repair was introduced.

## Implementation and custody

[observe_proposition.lean](observe_proposition.lean) is a scratch adaptation of
the existing formal observer. It checks local source/module/range ownership,
requires `ConstantInfo.defnInfo`, checks the selected declaration has type Prop
and its value is a proposition, then serializes the value. It uses a distinct
experimental helper/protocol label. Its output is not passed off as an existing
formal observation, native contract or admission receipt.

The original worker observes a declaration's **type**; for a definition of a
reading that would merely be Prop. The experiment deliberately observes its
**value**, without claiming the proposition is true. Generated selection ranges
identify the vocabulary file, not a paper theorem. The unchanged prior native
interpretation remains the owner of the authored paper span.

[ProseCases.lean](ProseCases.lean) begins with the exact previously checked paper
vocabulary and reading, then adds the unrelated control. [ProseAliasCases.lean](ProseAliasCases.lean)
preserves that whole file as a prefix and appends isolated alias controls. The
existing selected source and earlier evidence were not modified. Identity
comparisons and process commands are in [VERIFICATION.json](VERIFICATION.json).

One initial helper compile failed because two Lean Meta names were unqualified.
[failed-helper-1.lean](failed-helper-1.lean) and `selected-process.json` preserve
that attempt. The corrected helper was then used unchanged for all six semantic
probes. This initial compiler error is separate from expected shape rejections.

The experiment's existing renderer is recursive and is guarded here by the
whole process RSS/deadline/output limits; it has not been qualified as a bounded
production renderer. Production work must add expression-work limits, strict
request/owner validation, source/context mutation checks, historical replay and
public CLI error contracts. The scratch helper must not be shipped unchanged.

## Verification and review

Seven processes consumed 81.80s total measured process time, with peak
process-tree RSS about 5.02 GiB. All shared one 600-second absolute deadline and
the unchanged 12 GiB RSS/8 MiB output caps. No resource stop or clock reset
occurred. The run ended with remaining allowance; no larger-budget retry was used.

Integrity checks confirm 610 runtime files, 2,670 primary files, 67 prior
source-pair artifacts and 34 norm-bridge artifacts unchanged. No runtime,
repository test, dependency, build cache, paper or original formalization was
edited. No full suite was rerun. Nothing was committed or pushed.

Independent source/receipt review at board posts 1874–1875 confirmed the consumer
boundary; the reviewer did not rerun Lean. Final task/spec reconciliation is
retained in [REVIEW.jsonl](REVIEW.jsonl) and the reviewer artifact. An earlier
worker's unboarded claim that the existing prose producer sufficed was rejected:
it overlooked `validate_contract`'s `norm-scale-v1` restriction, and its follow-up
turn failed. No independent-review credit is assigned to that claim.

This closes only the bounded feasibility task after final review. It provides
no native Real prose production, predicate-law admission, source-fidelity
certification, mathematical refutation, whole-paper audit or detection-benefit
credit. The new child owns subsequent production work; parent Task 2.1 remains
open, including the separate generic transport/frontier acceptance requirement.
