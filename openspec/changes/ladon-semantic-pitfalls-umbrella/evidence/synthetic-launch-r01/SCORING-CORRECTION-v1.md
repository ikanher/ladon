# Synthetic comparison r01 scoring correction v1

Status: **accepted author reconciliation; independent review waived by the user**. Recorded 2026-11-13.

This addendum corrects interpretation of the frozen reports under the unchanged registration. It does not edit the original `RESULT.json`, `REPORT.md`, reviewer reports, receipts, or policy. Their SHA-256 values at correction time are recorded below.

## Governing rule

The policy-v2 registration (`synthetic-comparison-r01/REGISTRATION.md`, “Endpoints and adjudication”) defines a serious false accusation as asserting that a supported claim is false, or claiming an invalid witness establishes a fault, without qualification. It separately says ambiguous passages warrant preserved alternatives and abstention when the text does not select a reading, and that conditional analysis is scored on its actual reading.

## Unit-level reconciliation

| Unit | Control | Assisted | Reconciliation |
| --- | --- | --- | --- |
| 01 faithful original | Supported | Supported | Both bounded support judgments upheld. |
| 02 harmless paraphrase | Supported | Supported | Both bounded support judgments upheld. |
| 03 omitted state nonnegativity | Upheld fault; valid original-assumption counterexample | Missed fault; falsely reassured as supported | Control found the fault. Assisted is a false negative, not a false accusation under the registered definition. Both independent reference reviews used the phrase “serious false accusation,” but that label conflicts with the operative definition and the direction of the reports they describe. |
| 04 omitted dissipation nonnegativity | Upheld fault under the registered finite-total reading | Upheld fault under the same reading | Both reports give valid witnesses under the registered interpretation. Preserve their finite-sum reading. |
| 05 probability-scope ambiguity | Correct conditional support under almost-sure reading; intent unresolved | Correct conditional support under almost-sure reading; intent unresolved | Both reports explicitly qualify their support verdicts by the almost-sure reading and correctly match the theorem there. Neither establishes that the prose uniquely selects it. The assisted report’s claim that the formal conclusion “resolving the passage’s omitted qualifier” overstates that evidence: the theorem supports the selected interpretation but does not settle source intent. Record conditional support plus unresolved source scope. No report actually abstained. |

The unit-03 original-assumption witness is `X_n = -n`, `A_n=0`, `B_n=1`, `C_n=0` on a one-point probability space: the drift holds with equality and convergence fails. The original Lean theorem retains its `X` nonnegativity premise; this does not refute that theorem.

Unit 05 conditional credit follows the explicit registration clause that conditional analyses are scored on their actual reading. The reading-level match is upheld; unique source interpretation remains unresolved. Because neither auditor abstained, do not recode either as a warranted abstention. Report the conditional result and ambiguity limitation separately instead of collapsing them into a fully supported control or a false accusation.

## Corrected aggregate and gate

- Upheld useful fault findings: control **2**, assisted **1**.
- False negatives / false reassurance: control **0**, assisted **1** (unit 03).
- Serious false accusations under the frozen definition: control **0**, assisted **0** on the reviewed reports. This corrects the old assisted count of 1.
- Faithful controls 01–02 supported: control **2**, assisted **2**.
- Unit 05: one supported conditional reading per arm; source intent unresolved; no actual abstention in either arm.
- Additional independently upheld finding by assisted over control: **no**. Primary continuation gate: **not met**. Correcting the false-accusation category does not alter the finding counts or gate.

This is a source-level scoring reconciliation, not a fresh audit, new Lean certificate, causal estimate, or general accuracy claim. The experiment has one source cluster and one auditor realization per arm/unit. Treatment usage was exposed in reviewer cost inputs; describe reviewers as independent, not fully treatment-blind. Recorded command totals are 9 control and 45 assisted, including 2 and 21 help calls, respectively; summed command execution times are 57.516 and 99.404 seconds. These omit complete human/preparation/review effort, tokens, and exact active auditor time and do not establish that Ladon caused the difference.

## Provenance and review

Frozen source identities:

- Original aggregate: `RESULT.json`, SHA-256 `5d0e3fd4f6b6a16adf935047cbbb86b129e74b043c93d588ba0b5dc9089715de`.
- Original report: `REPORT.md`, SHA-256 `32a305380a259c274b7f63471921c1f0f9c38622362bc09aad7f6715aab9d53e`.
- Registration and every per-unit report/review remain separately bound by the existing packet/launch manifests and external workspace receipts; they are unchanged.

The two existing unit-03 reference reviews independently confirm the premise omission and valid fault finding, while calling the opposite-direction false reassurance a “serious false accusation.” This correction applies the registration's stated category definition. The two unit-05 reference reviews independently confirm the conditional almost-sure match and unresolved intended scope. Their reference-informed ratings should not erase the useful conditional analysis; neither should it erase the ambiguity. These existing reviews are evidence considered, not independent reviews of this correction document. The user subsequently waived separate independent review; N.3a closes on the recorded author reconciliation and current-session review.

## Author-review wording correction

The current-session review identified an inaccurate description of the unit-05 verdicts as unqualified. The row above now retains their explicit almost-sure qualification and locates the overstatement in the assisted report’s claim to resolve the omitted qualifier. The control’s advice to use the passage “as stated” is immediately qualified by “interpreting” the conclusions almost surely; that full qualification must be preserved. This wording correction does not change the counts or continuation gate. The subsequent user waiver closes the separate independent-review requirement.

## User waiver

The user instructed: “No need for independent review. Let's just continue.” This waives the separate review gate for this scoring correction. It does not convert the current-session review into independent evidence or alter any experiment result.
