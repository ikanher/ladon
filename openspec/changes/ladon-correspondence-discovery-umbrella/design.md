# Design

## Context

See [proposal.md](proposal.md) for the problem and [the contract](specs/ladon-correspondence-discovery/spec.md) for acceptance. This change targets Ladon; Quux is an external development source.

Observed existing behavior:

- `src/ladon/result_manifest_summary.py::_mapping_coverage` counts supplied claim components and links. It correctly calls this producer-declared coverage; it does not enumerate omitted passages in a document.
- `src/ladon/result_manifest.py` validates shape, revisions and references. `result_assessments.py` preserves attributed, revision-scoped judgments. The current review fields already support anchored assumptions, domains, quantifiers, conclusions and scope differences.
- `docs/RESULT_EXPOSITION.md` exposes exact target types and unmapped siblings, but structured parameter extraction is unavailable without a bound extraction owner. The source passage and component description remain authored interpretations.
- `docs/PROOF_CORRESPONDENCE_AUDIT.md` and the completed [r70 audit](../ladon-proof-correspondence-audit-umbrella/evidence/r70/README.md) already cover known examples, including the five-versus-four derivative estimate. They explicitly do not claim blind detection.
- Existing source-goal capture/completion, candidate checks and native ProofIR evidence can support local questions. A compiled theorem does not establish the interpretation of those questions.
- The Quux blind pass mapped Proposition 9.6 at construction-stage granularity and checked selected formal endpoints. Its later reveal identified mismatches at Lemma 8.6 and equation (10.19). This is an observed auditor/workflow failure, not evidence of a broken Ladon validator.

Planning provenance and original paths are in [sources.md](sources.md). Quux scratch files must be frozen into a Ladon-owned evidence directory during implementation before depending on their continued availability.

## Goals / Non-Goals

**Goals:** produce actionable local questions before a diagnosis is supplied; make unexamined source visible; check the direction of proposed mathematical implications; assess statement and method correspondence independently; measure whether Ladon reduces missed obligations or review cost.

**Non-Goals:** automatic semantic equivalence for unrestricted prose, formalizing the complete Navier–Stokes exposition, certifying arbitrary model reviews, adopting manuscript repairs, searching for further online criticism, introducing a mandatory model service, or reopening the completed r70 and older release qualifications.

## Decisions

### 1. Four work packages with a dependency order

| Package | Deliverable | Depends on | Exit |
| --- | --- | --- | --- |
| A: source coverage and triage | An attributed inventory of local assertions and uses, with an explicit unexamined population and a prioritized queue | Frozen baseline | Both known cases are inventoried without hiding their surrounding unexamined proof steps |
| B: quantitative contract comparison | Side-by-side mathematical contracts and exact missing implications; faithful controls | A | The derivative and pressure differences are explained without calling the informal estimates false |
| C: consumer-directed local checking | Checks or documented unresolved obligations tied to original local claims; an exercised audit recipe and any justified runtime child | B | Original goals, alternatives, assumption producers and method judgments remain separately inspectable |
| D: withheld discovery evaluation | One frozen comparison, case-level results and a decision on observed benefit | A–C frozen | All attempted cases, omissions and contamination are accounted for, including an unmet benefit outcome |

These are executable work packages within this umbrella, not placeholder child changes. A runtime child is created only for a concrete missing operation with a named consumer, observed failure and acceptance tests. It must use this umbrella's semantics and declare compatibility with the relevant existing command or schema. A documented manual route can complete A–C without any runtime expansion. The [work-package briefs](work-packages.md) specify deliverables and admission conditions.

### 2. Begin from the exposition, then find formal counterparts

Select an explicit section, theorem proof or page range. Inventory numbered claims, displayed estimates, applications of prior lemmas, limiting steps and existence assertions. Link supporting prose sentences and definitions. Record whether the inventory is machine-extracted, model-authored or human-reviewed, and retain ambiguity, exclusions and source spans not inspected. An inventory is a review product, never a proven exhaustive parse of mathematical meaning.

Retrieve candidate formal statements with local search and existing Ladon lookup. Follow all load-bearing premises of a selected application, including fields in premise-bearing structures and the constructions that supply them. A single dependency path is not a conjunctive proof. Preserve candidate alternatives and unresolved mappings rather than selecting the easiest theorem that reaches the same final conclusion.

Run a breadth pass before concentrating the remaining budget on a difficult slice. Prioritize explicit quantitative estimates, changes of domain or quantifier, existence/uniqueness claims, uniform limits and applications whose formal counterparts introduce additional premises. A high-priority queue guides attention but cannot suppress the remaining inventory.

Alternative rejected: begin with the compiled endpoint and generate an explanation. That can describe a correct replacement proof while never testing an intermediate sentence in the original exposition.

### 3. Compare explicit local contracts before asking Lean to solve anything

For each selected assertion retain:

- immutable source locator and literal assertion, with its context;
- an attributed interpretation with variable/object correspondence;
- hypotheses, domains, quantifier order and conclusion;
- for estimates: differentiated variables and orders, norm exponents, cutoff weights, parameter ranges and permitted constant dependencies;
- exact formal statement and its authority, plus relevant expanded definitions;
- the proposed implication direction and every missing premise or adapter;
- statement assessment, method assessment, evidence and unresolved questions.

Use ordinary readable files and existing assessment companions first. These fields describe the audit worksheet, not additions silently made to the closed v1 schemas. A possible future structured comparison must distinguish mechanically extracted formal data from interpreted prose, preserve original expressions and expose unsupported normalization. It cannot certify semantics by comparing strings.

The two primary development cases fix the required precision:

1. **Inverse estimate:** compare output order m with input m+4 versus m+5 in the same torus variables, at fixed other parameters, and constants uniform in the source function. Smoothness supplies existence of higher derivatives; it does not bound their size by a lower norm uniformly. The paper's stronger estimate may still be true. Inspect the power-three versus power-four Fourier summation argument before describing proof fidelity.
2. **Pressure flux:** retain the exact A_R/B_R dependence, cutoff powers, time quantifiers and R dependence. B_R bounded above by a function of A_R does not permit eliminating A_R from an upper bound. Both estimates may support uniqueness through different arguments. Identify the L^(3/2) Riesz route versus the L2/Sobolev route, without treating either as false merely because the methods differ.

Controls include alpha-renaming, definition expansion, a justified norm conversion, a stronger theorem that genuinely implies the requested claim, a changed constant that is harmless, a changed constant dependence that is not harmless, and a valid alternative proof. These protect against superficial difference detection.

### 4. Make the original local obligation the checked subject

Freeze the interpreted local goal before invoking candidate checking or source-goal completion. Attempt to supply the formal theorem's premises from the prose context and derive the required conclusion. Preserve remaining goals and unsuccessful attempts. If a proof engineer changes a premise, quantifier, norm or conclusion, it becomes a separate proposed repair, never completion of the original goal.

Formalize only the small missing implication when useful; reuse existing mathematical results. A Lean failure is evidence of an unsuccessful attempt, not a counterexample. An accepted adapter supports only its exact formal proposition; its relationship to the original prose remains an attributed judgment. Conversely, a conventional argument may justify correspondence without a Lean adapter, but must be labeled accordingly.

Inspect proof bodies for method claims and trace supplied premises to actual producers. Distinguish a generic interface that assumes estimates from the concrete construction that proves them. Checking an endpoint or obtaining an axiom list cannot replace this work.

### 5. Gate completeness of the workflow, not mathematical truth

An audit may finish with unresolved obligations and unexamined passages. Its completion checklist requires their visibility, the source and statement bindings for findings, explicit reasons for scoped conclusions, and distinct checking and review statuses. A report with no supported findings says that none were found in the named examined scope; it does not declare the selected document correct.

Reuse existing integrity and review-currency semantics. Do not make `reviewed-aligned` a machine-certified status or silently alter the v1 format. If operational use shows that a validator, summary or view omits necessary coverage, package the smallest consuming fix as a separate child. Preserve older evidence and treat changed source interpretations as new reviews, not hash-only renewals.

### 6. Evaluate both finding the passage and diagnosing it

The two revealed Navier–Stokes cases and r70 cases are development fixtures permanently. They are excluded from withheld scores even if placed in a fresh session. Preserve the blind Quux baseline as historical evidence with its original scope and failed detections; do not rewrite its result manifest.

Prepare a pilot of 12 withheld excerpts: six discrepancies spanning derivative loss, hidden premise, quantifier/domain drift, constant dependence, changed norm dependency and method substitution; and six faithful/equivalent controls. Separately prepare two longer source selections containing multiple candidate claims and at least one adjudicated discrepancy each. The longer selections test localization and omissions without giving the fault's line or lemma. Authored mutations and naturally occurring cases are reported separately; synthetic success does not establish real-paper effectiveness.

A curator freezes the reference diagnoses and supporting mathematical evidence before runs. Evaluation contexts and readable files exclude critiques, labels, previous audit outputs and answer-bearing comments. Fresh contexts alone are insufficient if filesystem access exposes answers. Use isolated input directories and enforceable access boundaries; if unavailable, retain the experiment as disclosed development work. State the limits of possible pretraining familiarity. Do not ask the current answer-informed auditor to certify its own blindness.

Compare competent ordinary tools with Ladon assistance using the same model configuration, source inputs, audit instructions, token allowance and wall-clock bounds. Each arm uses a separate context; randomize case order and prevent cross-arm answer sharing. Freeze configuration and scoring before the first result. Tool use is optional where it provides no benefit. No prompt tuning or repeated attempts against the scored set; a changed workflow requires a new withheld set.

Initial active-work limits are 20 minutes per excerpt and 45 minutes per longer selection per arm. Both arms share a separately recorded environment preparation step capped at 60 minutes and reuse compiled dependencies with their provenance disclosed. If preparation fails, use the same source-only constraints for both arms. Existing process supervision uses a 32 GiB process-tree RSS ceiling for Lean work. Record actual elapsed time, tokens, tool calls and interventions; budget exhaustion counts as incomplete work, not a clean result.

Score supported discrepancy localization, correct classification, false alarms on controls, missed reference claims, abstentions, and cost. A finding must identify the source assertion and formal counterpart or concrete unsupported inference and explain the discrepancy. A generic warning does not count as detection. A method difference reported as a false theorem is a classification error. Use the curator's reference inventory to score coverage, separately from the auditor's own declared inventory. Disputed reference answers remain separate until adjudicated.

Report paired per-case results and raw denominators. The pilot can support only a pilot-scoped benefit claim: more correctly supported findings without more false alarms, or equal findings/false alarms at lower observed cost. An inconclusive or worse result is retained. No broad accuracy or user-benefit claim follows from a small pilot. Stop after this run and analysis; do not loop until favorable.

### 7. Ladon ownership and Quux independence

Freeze minimal historical evidence from Quux into this change's implementation evidence, with source paths, digests, authorship and reveal status. Do not vendor its large target checkout or create a production import. Small reconstructed examples live in portable Ladon fixtures; real Navier–Stokes checks remain optional external integration cases with exact source/toolchain identities. The research target currently uses Lean 4.34.0-rc2; other fixtures must use their own compatible environments.

Any Quux prototype change requires its own Quux packet and is not a prerequisite for Ladon acceptance. Ladon runtime children must pass without Quux present. This umbrella neither changes the Quux active marker nor modifies prior Ladon qualifications.

## Risks / Trade-offs

- **Semantic interpretation remains the hard part** → expose the interpreted proposition and uncertainty; use independently prepared controls. More metadata cannot establish correspondence.
- **Inventory omits the fault before comparison begins** → score source selection separately from diagnosis and retain unexamined spans. Use the two longer selections to test this failure mode.
- **Runtime work is speculative** → first exercise A–C on both known cases and faithful controls within one working day. Admit a runtime child only with a concrete missing operation and consuming result; otherwise proceed with existing tools.
- **Local proof attempts consume the audit** → use bounded attempts and keep the unresolved queue; setup failures do not authorize silently substituting a different theorem.
- **Withheld answers leak through the shared workspace** → use an isolated input population and record accessible paths. If isolation cannot be enforced, do not make a withheld-detection claim.
- **Small or authored samples overstate practical benefit** → publish per-case results, distinguish synthetic from natural cases and retain the unmet outcome when real-source evidence is insufficient.
- **Same reviewer makes both translations** → preserve independent source assertions, exact formal statements and proof steps for challenge; a second model's agreement alone does not establish correctness.

## Migration Plan

This umbrella introduces planning and a consuming workflow contract. Existing commands and closed schemas are unchanged. Implementation first freezes evidence, then exercises the ordinary-file workflow and any justified child, and finally runs the frozen evaluation. Runtime children own their compatibility checks and rollback. Update the audit documentation to distinguish known-case reproduction from measured discovery only after evidence exists; keep historical records unchanged. A negative evaluation can close these tasks while explicitly leaving the larger discovery-benefit objective unmet.
