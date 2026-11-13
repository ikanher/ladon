# Bounded PLD source audit report

**Disposition:** bounded development audit complete; mathematical coverage remains partial. No mathematical fault was established, and this is not evidence of improved discovery or reduced cost from Ladon.

## What was examined

This exposed audit used the frozen PRV/PLD paper and appendix, surrounding definitions, selected DP-core Lean owners, and the centered Gaussian bridge note. The first inventory and interpretation were frozen before the fresh Lean check. The target math checkout was at f5b46eeee13e8f9d3cf161627c213a130241c593; all 15 selected inputs were clean at that commit and copied with matching hashes. The checkout had 161 unrelated dirty entries, which were not treated as selected sources. Inputs, Ladon runtime identity, toolchain, resource ceilings, and prior exposure are recorded in inputs/MANIFEST.json.

The fresh Lean command was a bounded scratch import/type query against already compiled imports. It exited successfully and printed the exact signatures and axiom reports listed in EVIDENCE.md. It did not rebuild the selected theorem owners, establish compiled-source lineage, replay an isolated capsule, or check the entire paper. Ladon's fresh lexical-fallback index was used only for navigation.

## Results and reader consequences

| Area | Audited result | What a reader may conclude |
|---|---|---|
| P2: privacy-curve characterization | The formal core supports a measurable-event/positive-region equivalence and a forward source-to-loss profile identity for strictly positive densities over a shared base. It does not cover the paper's exponential-smoothing formula or converse derivative reconstruction in this check. | The forward event algebra is available under its formal hypotheses. Do not infer a general mixed/singular-law result or the converse density recovery from these Lean declarations. |
| P4: independent composition | Lean checks an exact finite product-density realization as a family composition, under shared-base, measurability, positivity, and finiteness assumptions. The reviewer found no direct Lean theorem for the source's Gaussian PRV laws or the full general privacy-curve statement. | The finite product instance is supported. The broader source theorem still needs an explicit object/law map and proof. No contradiction was found. |
| Gaussian control | Lean checks the one-way implication from the analytic scalar condition to the event-level centered Gaussian approximate-DP inequality under σ > 0, ε ≥ 0, Δ ≥ 0, squared distance ≤ (Δ/2)^2, and δ < 1. | This is a justified control for the scalar-to-event direction with those premises. It is not evidence for maximizing half-space equality, endpoint sharpness, or the note's radial envelope. |
| P1/P3 and remaining Gaussian assertions | Not established by the bounded check; see inventory and reconciliation. | No claims about arbitrary-law PRV existence, derivative inversion, uniqueness, or full Gaussian note coverage. |

The independent reviewer agrees with these scope limits and classifies P2's converse as a formalization/scope gap, not an established mathematical fault. The reviewer also confirms the one-way Gaussian control boundary. Full attributed dispositions are in RECONCILIATION.md; first findings remain preserved in FINDINGS.md.

## Ladon's contribution and cost

Ladon helped navigate to candidate theorem owners and their exact names through its local lexical index. That index was not proof authority. The decisive checks were performed by ordinary Lean against the selected compiled imports; mathematical source reading and reviewer comparison established the source-to-formal scope distinctions. This run did not exercise a novel Ladon diagnostic operation, prove that Ladon selected the right obligation autonomously, or measure a comparison against ordinary Lean plus the same LLM and recipes. It therefore establishes no comparative product benefit.

The recorded effort ledger separates input/inventory, checking, and independent review. The actual run stayed within its 60-minute checking ceiling and 12-GiB process-tree cap; one heavy check ran at a time. No memory stop occurred. An initial theorem-name guess was incorrect. The successful corrected query and its output are preserved; the raw output from that failed first lookup was not captured, and the effort ledger records the attempt.

## Scope, decision, and next step

The audit supports the limited conclusion that existing Lean owners provide useful local forward PLD identities, a finite product composition result, and a one-way Gaussian scalar-to-event theorem. It leaves the broad PRV representation/converse and full Gaussian extremal statement unresolved. The reviewed evidence does not show a concrete missing Ladon operation; the main gaps are mathematical coverage and exact correspondence. Do not implement a general PRV adapter or expand schemas on this evidence alone.

If this research path continues, the next useful step is to select one unresolved assertion whose exact assumptions and source meaning can be stated, then decide whether a conventional proof/source comparison suffices or whether a formal theorem is genuinely needed. A fresh matched comparison requires its own frozen registration, baseline, budget, and practical success threshold. The known-fault Navier–Stokes regression remains separate and is not started by this report.

## Evidence identity

- Frozen selected inputs: inputs/MANIFEST.json (SHA-256 e82b50bb862c1780c826f1ce1848121241d525fdff9ae1a42f9f2a916614c2bf)
- First inventory: INVENTORY.md (SHA-256 e22601ec6322fe149824095ad6bf73c28251c8f2fa45111bdec7706fe9fa9743)
- First findings: FINDINGS.md, frozen before review (SHA-256 72f3579266002dea748dc14bc0b41761d2ab431caf4828597c8951c87ca22e3b)
- Fresh Lean check: work/AuditCheck.lean; complete output work/audit-check.log
- Independent source review: review/REVIEW.md
- Review reconciliation: RECONCILIATION.md
- Actual effort record: EFFORT.json

The files listed above and their current SHA-256 values are captured in work/REPORT-MANIFEST.json.
