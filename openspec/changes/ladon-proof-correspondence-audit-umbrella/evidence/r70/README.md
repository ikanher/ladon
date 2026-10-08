# r70: correspondence audits from known development cases

Three elementary examples now have separate ordinary Lean checks and faithful controls. The one published derivative comparison has source-local evidence and an explicitly unresolved stronger-estimate bridge. These are root-authored audits of already explained examples, not independent model detection or comparative reader experiments.

| Question | Scoped outcome | Support |
|---|---|---|
| Does the polynomial argument prove its conclusion? | No: its factorization and sign claim fail at zero. The unchanged final inequality is true by the corrected factorization. | [Source and witnesses](cases/Polynomial.lean), [accepted run](runs/polynomial-01/record.json), [wrong-step residual](runs/polynomial-wrong-step-01/stdout.txt) |
| Does the least-element definition establish existence? | No: the concrete defining set is empty; Lean chooses zero and the algebra still checks. A nonempty-set variant explicitly preserves existence. | [Separate obligations](cases/LeastElement.lean), [accepted run](runs/least-element-02/record.json) |
| Is the different matrix proof false? | No: both the direct-symmetry and diagonalization proofs check. The direct proof does not formalize the supplied change-of-basis steps. | [Both routes](cases/Matrix.lean), [accepted run](runs/matrix-02/record.json) |
| Does the cited inverse estimate establish the paper's four-derivative-loss bound? | The inspected theorem requests five additional derivatives. No same-constant four-loss bridge is supplied or checked here; this does not refute the four-loss estimate. | [Published comparison](PUBLISHED_COMPARISON.md), [pinned sources](sources/navier/inventory.json) |

The [walkthrough](AUDIT_RECIPE.md) gives the exercised ordinary-file route. [Corrections](CORRECTIONS.md) preserve original and proposed arguments. [Interventions](INTERVENTIONS.md) disclose reconstruction errors, warnings and unused capabilities. [Review handoff](REVIEW_HANDOFF.md) states the stopping decision.

Source identities and provenance are in the [frozen inventory](source-inventory.json) and [case inputs](cases/FROZEN_INPUTS.md). Original source snapshots are retained; none of the proposed prose has been adopted by the responsible authors. Judgments about correspondence are attributed to the root audit, not generated or certified by Ladon.

## Checking and access

Reading the Markdown, Lean sources and saved outputs needs no model account. Fresh elementary checks used Lean 4.33.0 and Mathlib `db584cd6d46c92f209a44c0f1c829460d327499d`; see [environment](environment/README.md). Ordinary compilation and printed transitive axioms were checked for the named audit declarations. Imported compiled libraries were copied, not independently adversarially validated.

The 32 GiB limit is sampled aggregate process-tree RSS through Ladon's existing supervisor. Every check stayed below it; the largest recorded attempt used about 7.2 GiB, dominated by the full Mathlib import in the least-element file. These short runs are not benchmarks. [Run inventory](run-inventory.json) includes successful and unsuccessful attempts. An error can leave `sorryAx` in Lean's diagnostic declarations; those failed attempts are rejected, not promoted by later algebraic output.

The Navier–Stokes source requires a different pinned toolchain and Mathlib population. It was not compiled here. Its actual imports and replay limitations are recorded in the comparison; the elementary environment is not a substitute.
