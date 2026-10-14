# Investigate an exposition without a supplied diagnosis

Begin with the original exposition and its existing formal source. Preserve input identities and state the selected source range and work budget. Keep the original mathematical assertions unchanged throughout the investigation. Treat interpretations, candidate matches and repairs as separate work products.

## Maintain the investigation loop

Use [the source-bound investigation commands](INVESTIGATION_LOOP.md) to initialize a plan at the actual start, with the selected source and explicit budget. After each batch save a numbered plan snapshot, run `ladon investigation next`, and continue actionable work. Do not end merely because a few comparisons found no issue. Run `finish` before the final report; a `continue` result requires further work within the remaining budget. Record budget exhaustion, evidenced blockers or explicit user cancellation as incomplete outcomes. The controller validates authored bookkeeping, not mathematical meanings or inventory completeness.

## Make a source inventory before choosing a proof slice

Read the selected exposition broadly first. Record each stated result, intermediate assertion and use of an earlier result that you identify. Include assertions carried by displayed expressions and surrounding prose. For each source span, record whether it was examined, interpreted, matched to formal support or left unresolved. Keep unexamined passages visible.

An authored inventory is not guaranteed to capture every mathematical assertion. Say how it was prepared and whether its completeness has been independently reviewed. Mapping every supplied component does not establish that every source assertion was supplied. Account for source coverage before summarizing mapping coverage.

Choose follow-up questions from the inventory, with reasons based on the mathematical role and missing evidence. Keep the rest of the queue. A difficult local proof should not consume the budget without leaving a visible record of the claims it displaced.

## Compare the exact local claim

Find candidate declarations using ordinary source search or Ladon's declaration lookup. Inspect the full type and the definitions it uses. Search results are navigation evidence; an empty search is not proof of absence.

Write a side-by-side comparison for each questioned step:

| Item | Exposition | Formal support | Justification or open question |
| --- | --- | --- | --- |
| Objects and their correspondence | | | |
| Assumptions and their source | | | |
| Parameter domains and quantifiers | | | |
| Exact conclusion and dependencies | | | |
| Needed implication | | | |
| Actual argument | | | |

For quantitative claims, expand all relevant orders, exponents, weights and permissible constant dependencies. Preserve the original expressions. A naming change or a different representation can be harmless, but requires a reason. Conversely, a similar-looking result can require a stronger premise or provide a weaker guarantee.

Ask two separate questions: does the formal result support the local assertion, and does its argument support the reasoning described in the exposition? A valid alternative argument may support the conclusion while leaving the claimed method unsupported.

## Resolve a suspicious derivation before expanding the inventory

Use [local derivation challenges](DERIVATION_CHALLENGES.md) when the source and its proposed support differ. Start a version-two plan with `--derivations`; split the disputed argument into source-bound steps, explicit rules and substitutions. Give a sanitized packet to an independent challenger. Record a supporting derivation, a premise-satisfying counterexample, or the exact remaining obligation. A judgment that the argument “looks consistent” does not supply those steps. Prioritize concrete gaps over collecting more headings, and use the exact rational witness command when the local implication fits its supported fragment.

## Follow the application in the required direction

Name the implication needed at the precise point of use. Check both whether the prose context supplies the formal result's premises and whether the result supplies the conclusion the next step requires. For structured premises, inspect the relevant fields and the actual constructions that establish them. Do not stop at a generic theorem that accepts those fields as inputs.

Do not reverse a one-sided implication or comparison. A final theorem cannot justify a questioned stepping stone retrospectively. Preserve unavailable formal support and candidate alternatives instead of selecting a convenient replacement with the same endpoint.

## Check the original obligation before repairing it

When local formal checking helps, freeze the interpreted goal and context before applying a candidate. Use ordinary Lean, explicit candidate checks or source-goal completion as appropriate. Retain the exact source, command, environment, output and remaining obligations.

Adding a premise, changing a quantified domain or weakening a conclusion produces a separate proposed revision. An accepted check of that revision does not finish the original obligation. An unsuccessful tactic or application is not a refutation; a counterexample needs its own evidence. A conventional justification can be useful without a formal adapter, but label its authority accurately.

Read relevant proof bodies before judging method correspondence. Axiom inventories, source associations and dependency navigation do not establish a mathematical argument's fidelity.

## Finish with findings and explicit omissions

For each finding, retain its source location, exact interpreted assertion, proposed formal support, reason, evidence and uncertainty. Separately report statement and method judgments. Keep checking outcomes distinct from attributed reviews and from artifact integrity.

Report examined source spans, unmapped claims, unresolved applications and unexamined material. If no issue was found, state that result for the examined scope. Save the first report before receiving a reference answer and put later reassessment in a new record.

This procedure is usable with ordinary files and installed tool help. It does not certify source-inventory completeness or automate mathematical correspondence. Testing whether it improves detection requires fresh evaluation contexts whose accessible inputs exclude reference answers and prior analyses.
