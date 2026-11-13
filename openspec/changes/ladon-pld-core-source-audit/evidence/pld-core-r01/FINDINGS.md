# First findings (frozen before independent review)

Status: first report for exposed development audit; not blind discovery. Inputs are frozen in `inputs/MANIFEST.json`. The first interpretations are `INVENTORY.md`. Evidence is `EVIDENCE.md`; raw Lean check is preserved in `work/`.

## Findings table

| ID | Source claim | Formal/use evidence | First disposition | Reader consequence / remaining question |
|---|---|---|---|---|
| P1 | General PRV pair definition and change-of-measure statement. | No fresh check of mixed, zero-density or singular cases. | Unresolved / not checked. | Do not treat the positive shared-density bridge as a general RN derivative theorem. Need review of exact source definitions and assumptions. |
| P2 | Likelihood-ratio variables represent the ordered privacy curve. | Event/profile iff and positive shared-density source-to-loss identity check against existing owners. | Partial formal support; full scope unresolved. No exposition error established. | These results substantiate a useful event-algebra layer. It remains to verify that source P/Q direction, strict threshold and law assumptions map precisely, and identify any unsupported generality. |
| P3 | Tail/expectation formulas and converse derivative reconstruction. | No derivative or uniqueness theorem checked. | Unresolved / not checked. | No reader should infer the inverse reconstruction from the checked event iff. Regularity and endpoints need a separate exact analysis. |
| P4 | Independent composition adds paired privacy-loss variables and represents composed privacy curves. | Exact finite product equality to `PLDPair.compFamily` checks for shared-base finite strictly positive densities. | Supported for that formal product-density instance; broader source claim unresolved. No exposition error established. | Reader gets an exact reusable composition result on stated conditions; arbitrary PRV/curve generality still needs the object map and independence correspondence. |
| G1/G2 | Gaussian half-space event and radial/scalar reduction. | Analytic condition iff standard-normal interval-event form checks; selected source theorem-level bridge not yet established. | Unresolved control candidate; not counted as passing. | A useful control requires confirming the note's event, radius and scalar envelope against the formal endpoints. |

## Overall first assessment

The existing DP core supplies real formal evidence for event-profile algebra and exact finite composition of positive shared-base density laws. It does not, from this bounded check alone, settle general PRV representation, converse differentiability, or the selected Gaussian reduction. The scope restrictions are mathematically material and need an independent source review before treating the exposition as matched or mismatched. **No mathematical fault has been established.**

Ladon helped locate the local theorem owners and identify the exact product-composition declaration; ordinary Lean established the inspected types and axiom lists. Source reading established the paper's displayed statements and proof spans. This single exposed audit does not show that Ladon improved discovery or reduced effort. No measured comparison was run.
