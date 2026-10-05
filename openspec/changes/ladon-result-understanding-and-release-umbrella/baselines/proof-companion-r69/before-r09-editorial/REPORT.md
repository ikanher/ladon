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
- COMPANION.md and COMPANION_CORRECTION.patch show the explanatory change.
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

## Stopping point and next review

The bounded handoff is ready. Do not manufacture another question, launch a new
uptake experiment, or optimize the next function automatically. Ask the same pro
to assess the explanation's fidelity, the limited interaction evidence, and
whether any concrete next work follows toward community understanding and reuse.
Maintainer editorial adoption remains a separate decision. The umbrella remains
33/50 with its earlier benefit gate unmet/deferred. r68 maintenance is accepted
and its small filtered-harness fix is recorded separately.
