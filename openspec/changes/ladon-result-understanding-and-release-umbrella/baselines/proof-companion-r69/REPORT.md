# r69 — fixed-epoch explanation and proposed correction handoff

Following r08, the user selected the existing fixed-epoch exposition. A focused
companion explains its offset specialization, including exact calibration
identity and horizon substitution. The user then asked why variance divergence
needed to be stated or proved. That actual question led to an explanatory revision.

## What changed

The companion now distinguishes decreasing raw noise from diverging normalized
privacy variance. The identity is $v_{E,T}=T\sigma_{E,T}^2/E^2$: increasing $T$
alone does not determine the product because noise is recalibrated. The theorem
establishes the logarithmic decay, so the divergence follows by elementary
algebra. It matters for eventual full-batch dominance and differs from the
bounded average-only calibration. The conditions remain fixed positive E,
positive sensitivity, nonnegative epsilon and delta strictly inside the stated
nonparticipation boundary.

- COMPANION_BEFORE_QUESTION.md preserves the draft before the question.
- READER_QUESTION_AND_RESPONSE.md preserves the actual question, response and
  user's follow-up: “Sure, do continue then.”
- COMPANION_CORRECTION.patch preserves the original question-driven change.
- before-r09-editorial/ preserves the submitted r09 explanation and proposal;
  R09_EDITORIAL.patch records the subsequent reviewed refinements to the live files.
- ORIGINAL_PASSAGE.tex preserves the existing manuscript proof paragraph.
- PROPOSED_PAPER_PARAGRAPH.tex offers a short editable clarification after the
  sparse-calibration theorem; it is not adopted or inserted in the real project.
- SOURCE_SUPPORT.md records source identities, historical support, and the
  ordinary checking route. Reading and proposing corrections need no model access.

## Evidence and limits

The clarification is conventional mathematical exposition checked against the
existing formulas and statements. No new Lean check was needed or performed;
this handoff does not renew current imported dependencies or compiler evidence.
The proposed adapter's source digest matches its historical compilation receipt.
No new canonical registration, current correspondence review or coverage upgrade
was created. Offset checking does not promote leading/variance/average components.

The user's acknowledgment permits continuation. It is not a measured reader
comprehension result, independent review of the full companion, or adoption by a
mathematical maintainer. No reader credentials or general understanding were
inferred. There is one real question and a concrete proposed explanatory change.

This offers a narrow mathematical/editorial contribution. Direct documents and
source inspection sufficed; no Ladon mathematical command was invoked and no
comparative software or artifact-maintenance advantage is established. No
recurring software handoff defect was exposed by this interaction.

## r09 editorial follow-through and closure

The returned review accepts the clarification as a narrow editorial contribution.
The revised companion now explains why divergence alone has a shorter proof:
for any fixed candidate normalized variance, a threshold event detects at least
one participation with limiting probability exceeding delta. Gaussian tail
errors vanish. This conventional reviewer-supplied argument does not give the
sharp logarithmic rate, a numerical cutoff or new formal checking evidence.

The hypothetical inverse-square-root noise schedule is explicitly algebraic,
not feasible transcript calibration under the stated conditions. The explanation
preserves E-normalization, fixed parameters, the strict delta range, uniform-in-S
eventual comparison, and the limited average-only feasibility bound.

PROPOSED_PAPER_PARAGRAPH.tex is offered to the responsible mathematical author
as a replacement transition, retaining the bracketing explanation and removing
the redundant old dominance sentence. ORIGINAL_TRANSITION.tex preserves the
source transition. No mathematical-project files were changed. Adoption remains
pending; any adopted manuscript revision needs its own revision-bound assessment.
The historical assessment is not a review of this companion or new paragraph.

SOURCE_SUPPORT_PACKET.md links to unchanged, already-disclosed r09 supporting
sources copied into supporting-sources/ for portable reading. The full imports,
compiled dependencies and audit module remain omitted. These copies do not make
this a self-contained checking environment or renew historical evidence.

## Stopping point and next review

This explanation-and-correction cycle is closed as a reviewed, unadopted proposal.
Record the author’s decision when available; do not require another reader reply
or routine pro review. The umbrella remains 33/50 with its benefit gate
unmet/deferred. r68 maintenance remains closed. No runtime source changed.

Resume substantive development or review only for a new mathematical question,
a material claim/support change, or a concrete costly or error-prone handoff in
actual use. Do not manufacture another question, uptake experiment or automatic
optimization target. Editorial value and software advantage remain distinct.

## Editorial verification

The umbrella passes `openspec validate
ladon-result-understanding-and-release-umbrella --strict`. All 13 local links
in the companion and its two support notes resolve. All 14 copied supporting
files are byte-identical to the previously supplied r09 archive staging sources.
The four pre-editorial snapshots match the submitted copies, and the original
r09 ZIP digest is unchanged. Paragraph references resolve to existing source
labels, and the preserved original transition occurs exactly once there.
These are document/navigation/identity checks, not TeX compilation, a fresh Lean
check, renewed product qualification or certification of prose correspondence.
