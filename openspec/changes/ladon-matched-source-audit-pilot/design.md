# Design

## Context

See [proposal.md](proposal.md) for motivation. The recent source-consistency qualification was a supplied-obligation test on authored rational fixtures, not discovery. The existing correspondence guide supplies manual audit recipes; the pilot must measure their use without giving either arm an unfair prompt, source, or time advantage. Several previously discussed mathematical sources and diagnoses are already exposed to this project and cannot count as fresh discovery evidence.

## Goals / Non-Goals

**Goals:**

- Determine whether access to the thin Ladon workflow adds useful source findings or reduces total review effort at comparable finding quality.
- Keep interpretation, formal checking, and reader usefulness observable as separate stages.
- Produce enough frozen evidence for an independent reviewer to reproduce the comparison and challenge adjudications.

**Non-Goals:**

- No production feature, broad semantic schema, or new detector is implemented by this evaluation packet.
- No general claim that Ladon proves natural-language/formal equivalence or reliably finds mathematical errors.
- No credit for rediscovering known diagnoses, previously exposed source claims, or supplied obligations.

## Decisions

### Paired, fresh source/Lean units

Use six to eight short units drawn from existing source material with compiling formal counterparts. Prefer distinct proof claims or passages that can be evaluated independently. The source-selection record must include exact paths and line spans, Lean declarations and toolchain/environment identity, hashes, dependencies needed to check the claims, and a disclosure log. Exclude the known PRV density-sign discrepancy, its repaired formula and controls, the PLD audit, the authored scalar qualification fixtures, Navier–Stokes material, the already discussed DP-SGD/GDP target, and any other unit whose diagnosis or answer was exposed to the participants. If fewer than six eligible units remain, stop and report the shortage rather than fill the sample with known answers or newly authored mutations.

Multiple units may come from one exposition when their formal claims are separately checkable. Register source-note clusters and report per-unit evidence within those clusters; do not present the six claims as six independent papers or use the small sample for inferential statistics. Broad topic familiarity is disclosed even when a specific claim has not been discussed.

Prefer faithful material, cases where a careful reader should abstain because the text is ambiguous or underspecified, and naturally occurring questionable intermediate claims when an answer-blind selector can select them without classifying correctness or leaking a diagnosis. Selection itself must not pre-label correctness. If the frozen eligible sample does not have known faithful/ambiguous/fault coverage, report this limitation; blinded adjudicators determine which categories are actually represented. Do not add cases after seeing arm outputs. Label any constructed mutation separately; it cannot establish discovery benefit. An independent selector should certify only that selection was answer-blind.

### Matched arms and isolation

Both arms receive the same allowlisted source/Lean capsule, model identity and settings, audit recipe, prompt framing, Lean/toolchain access, wall-clock and Lean-invocation ceilings, and instructions for abstention. Token telemetry is recorded only if exposed by the runtime; do not claim a token ceiling when none can be enforced. The only intended treatment difference is access to Ladon's existing source-linked capture, checking, and evidence-reporting workflow. The control arm may use ordinary Lean and the same recipes. Do not give either arm a selected-unit manifest, selected formal obligation, counterexample, diagnosis, or answer key. If a supplied-obligation stage is useful, register it as a separate secondary track and do not pool its results with discovery.

The capsule contains only registered source spans, the corresponding Lean declarations/modules, required import/build metadata and dependencies, and the common audit recipe. It excludes prior audit reports, OpenSpec evidence, sidecar answers, unrelated repository text, and the selector's notes. Validate the capsule manifest and hashes before each arm. If an import dependency forces access to excluded answer-bearing material, either construct a smaller checkable capsule or exclude that unit before registration.

Run each arm in separate fresh model contexts and separate output directories. The available agent environment does not enforce filesystem isolation, so isolation is procedural: give each arm only its input-capsule path, instruct it not to inspect registration/evaluation material or any other project files, and disclose this limit in the report. Freeze and timestamp each first report before either arm or reviewer sees the paired report or adjudication material. Randomize arm order and blind adjudicators to arm identity where practical. Preserve prompts, available tool transcripts, Lean/Ladon outputs, reported timing, observable token data, retries, errors, and resource-limit events. Mark unavailable telemetry unavailable. Treat missing or failed extraction/replay as a measured outcome, not as a mathematical refutation.

### Independent adjudication and scoring

An answer custodian, separate from the two audit arms, holds source interpretations, expected findings, and any diagnosis material. Before unblinding, independent reviewers assess every alleged finding against the exact source and Lean evidence, and assess controls/abstentions. Record upheld useful discrepancies, false accusations (with severity), justified controls, warranted abstentions, interpretation errors, formal-check failures, and unresolved judgments separately. An unresolved judgment earns neither finding credit nor false-accusation credit until resolved.

Measure the full cost to a comparable result: preparation and source qualification, model interaction, Lean attempts, interpretation and review, adjudication, elapsed time, tokens, and any human corrections. Report per-unit and aggregate paired results; do not hide setup or reviewer effort. State exclusions and missing measurements.

### Success and stop decision

Because the current project objective is mathematical discrepancy detection, preregister one primary criterion: Ladon produces at least one additional independently upheld, reader-useful source finding across the paired units, with no new serious false accusation compared with ordinary Lean plus the same recipes. “Useful” requires a stated consequence for the source's mathematical claim or its reader; a raw formal mismatch is insufficient. Cost reduction at matched finding quality is a secondary descriptive outcome in this pilot, not an alternative success gate. Report all cost components so a later study can set a defensible threshold. No endpoint may be changed after observing results.

Stop before launch if a comparable six-unit set, isolation/custody, independent adjudication, or the chosen primary criterion cannot be secured. Stop at the registered resource budget; report exhaustion and partial outcomes without extending budgets selectively. A positive pilot warrants a larger study, not general reliability claims. If ordinary Lean plus the same recipes yields equivalent results at lower total cost, or if Ladon causes serious false accusations, record that as evidence against expansion.

## Risks / Trade-offs

- **Prior exposure contaminates discovery** → use a disclosure log and exclude any source/claim/diagnosis known to either arm; use fresh contexts and preserved first reports.
- **The evaluator selects easy or known examples** → freeze a candidate pool and selection rule before answers are inspected; ask an independent selector to attest to eligibility.
- **Unequal effort masquerades as a tool effect** → match prompts, recipes, tool availability, and budgets; account for preparation and human effort.
- **Reviewers infer arm identity or favor one workflow** → mask arm labels and report unavoidable cues; use independent adjudication with recorded rationales.
- **Small sample yields unstable results** → treat this as a decision pilot only; publish per-unit outcomes and do not generalize from aggregate percentages.
- **Several units share one exposition or proof module** → disclose and report by source cluster; avoid treating claim counts as independent sample size.
- **The full repository exposes prior answers** → provide each arm the same allowlisted capsule and verify no answer-bearing sidecars or history are reachable.
- **Material or threshold is unavailable** → do not launch. Resolve through a bounded eligibility inventory and an owner preregistration decision.

## Migration Plan

No product migration. Create a revision-bound pilot directory under the change’s evidence tree. Before launch, freeze registration, source manifest, arm instructions, budget, answer custody, adjudication rubric, and success criterion. After completion, freeze both arms’ first reports, adjudications, cost ledger, and final decision report. Do not amend the registration after observing outcomes; any changed design requires a new pilot identity.

## Open Questions

- Can a fresh source inventory produce a fault-bearing, independently adjudicable exposition/Lean pair plus faithful controls and a genuine ambiguity/abstention case, without exposing its diagnosis to the audit arms?

## Post-pilot evidence update

The first registered run is recorded in
[`evidence/run-20261113-r01/REPORT.md`](evidence/run-20261113-r01/REPORT.md).
Six claims across two source notes were eligible and checkable, but after
adjudication all six were faithful correspondences. Both arms reached that
result; neither produced an upheld discrepancy or serious false accusation.
The primary gate was therefore not met. Ordinary Lean plus the same recipe
used less measured run time and fewer Lean/Lake invocations, while token,
preparation, and adjudication costs remain unavailable. This is a negative
result for this sample, not a measurement of sensitivity to real exposition
faults.

The notes themselves include source-to-Lean crosswalks, so this run measured
verification with suggested declaration mappings available rather than
unaided mapping discovery. The Ladon arm used text architecture analysis; it
did not use native capture, proof extraction, or completion evidence. The common
recipe was matched across arms but did not explicitly include the full
definition-substitution, object-map, and premise-realizability steps qualified
in the parent S.1–S.3 work. The result therefore does not establish the value
or failure of those unused capabilities or the complete developed recipe.

The subsequent planning review places [umbrella N.1–N.2](../ladon-semantic-pitfalls-umbrella/tasks.md)
before any new run: qualify one useful existing evidence route using the
completed development work and receipts, then prepare a separate comparison
only if that route contributes useful evidence. A challenge should include a
fresh, independently confirmed natural exposition fault held by a separate
answer custodian, faithful controls, and a real ambiguity case. Define whether
the treatment is optional tool access or an instructed evidence workflow;
record actual uptake and provide both arms the same complete mathematical
recipe. If unaided mapping is the target, select an exposition that does not
include its formal crosswalk. Keep the answer and fault location away from
both arms. The frozen pilot remains complete and unchanged; these are
conditions for a separately registered study, not retrospective changes to
its gate or results.
