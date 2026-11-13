# Execution recipe for M.2 and review recipe for M.3

## Outcome and scope

Deliver one report that explains, for A–D, what premise the original proof uses, where that premise comes from, and whether the passage discloses or establishes it. M.1 has frozen inputs and first interpretations. M.2 produces evidence rows and first conclusions; M.3 reviews them. No production implementation is needed to begin.

Routine input verification and evidence collection are suitable for a cheaper agent following these steps. A mathematical reviewer decides disputed interpretation or evidence adequacy. Keep those roles distinct; a model's confidence is not evidence.

## 1. Verify the inputs

Work from `/home/codex/projects/ladon`, using the checkout. Run:

```bash
sha256sum --check openspec/changes/ladon-premise-provenance/evidence/premise-comparison-r01/SHA256SUMS
```

Every entry must match. If one does not, stop work on the affected case and report the path; do not regenerate the manifest or substitute current sibling sources. Read README.md, PASSAGES.md, then CASES.json. CASES.json contains exposed expectations, not checker results. All references are repository-relative. Read each entire small Lean fixture; for D read the cited TeX spans, the entire GaussianStep theorem, and the moment hypotheses in OneStep.

Create a new output directory under `openspec/changes/ladon-premise-provenance/evidence/` with a distinct run identifier. Fail if it already exists. Record the input-manifest hash, current Git HEAD/dirty state, start time and executor. Do not put results inside this frozen directory.

## 2. Collect the formal evidence without inventing new authority

Start with the retained slices listed per case. Their compilation provenance is already inspected in INPUT-CHECK.json. This is reuse of historical evidence; no new Lean execution is implied. A and B intentionally share the same slice and theorem.

For A and B:

1. In the slice's `nodes`, select the application of `PitfallCorpus.HasConclusion.proof` at occurrence 0.
2. Inspect `arguments[1]` and its structural expression. Match its fvar ID to `localContext.localId`; record the exact local type, binder kind and absent `letValue`.
3. Read the definition of `HasConclusion` in the frozen `Pitfalls.lean` and the theorem's full telescope. Record the field type and caller-supplied assumption.
4. Report the same formal route for A and B. Any difference between their source judgments must come from the passages, not from implicit/explicit binder syntax or a changed Lean proof.

For C:

1. Inspect the selected `HasConclusion.proof` application and provider argument in its slice.
2. Match the provider's qualified identity to the definition in `premise_provenance_04.lean`.
3. Record the constructor's `arithmeticFact` argument and its independent `by decide` theorem, including the source lines. A class projection by itself is insufficient to classify this as an assumed conclusion.
4. State which parts are original-term observation, source inspection and retained compilation evidence. Do not describe source inspection as a newly replayed provider proof.

For D:

1. Use ROUTE.json as navigation into `slice-attempt-05.json`, not as a substitute for that slice. Confirm the source hash, selected declaration/application, occurrence and scope path agree.
2. Locate argument indices 35 and 36 in the selected application. Compare their structural fvar references to the corresponding scoped locals and their values. Preserve the energy argument's wrapper.
3. Match the local values to `gaussian_direction_mean` and `gaussian_direction_energy` in the frozen GaussianStep source. Keep its entire assumption telescope available; this is not unconditional descent.
4. Record provider-boundary and provider-unreplayed frontiers. Limit the conclusion to those two premises in that selected application. Other assumptions, whole-proof coverage, privacy calibration and scientific feasibility are outside this case.

Structural expressions use the `ladon-expr-dag-v1:` prefix followed by JSON. Compare exact fvar/constant identities and follow the root's references; matching printed names or finding an unrelated occurrence elsewhere is insufficient. If the representation or scope is unclear, preserve the raw location and refer the question to mathematical/technical review. Do not guess a binding.

## 3. Compare each route with the source

For each case answer these questions in order:

1. What precise assertion does the passage make, and under which stated premises?
2. What does the selected formal theorem require?
3. Where does its actual proof obtain the selected premise?
4. Does the passage disclose that assumption or justify its construction within the declared scope?
5. What does the evidence establish, and what remains unresolved?

For A, the complete standalone scope is part of the input. Do not invent an earlier provider or automatically assume type-class search can construct one. For B, disclosure in prose counts even though Lean uses an instance binder. For C and D, check the provider route instead of treating every premise parameter in an intermediate theorem as an error. An omitted-premise discrepancy does not invalidate the conditional Lean theorem. Do not claim necessity or circularity without separate evidence.

The expected distinctions in CASES.json are hypotheses to substantiate. If evidence contradicts them, record the disagreement without changing the frozen input. If a source reading is ambiguous, quote the competing readings and retain an unresolved interpretation for review.

## 4. Write the first report and preserve it

Create `FINDINGS.md` with one row per case containing:

- input ID and exact source span;
- attributed claim and preserved assumptions;
- actual-use evidence with JSON/source locations;
- checked projection evidence, if available, labeled historical or fresh;
- source-justification assessment;
- outcome: supported discrepancy, justified control, or unresolved;
- precise reader consequence and coverage limits.

Include an effort ledger for preparation, inspection/checking and review, with command outcomes and measured times where available. Report new Lean attempts as zero if none were run. Reusing previously paid extraction work must not appear as a zero-cost end-to-end workflow. Record what Ladon contributed: for example, an explicit argument/local binding or a visible unresolved frontier. No comparative benefit can be claimed without a matched comparison.

Hash the first report before review. Record later corrections as an addendum. Do not rescore the historical baseline or count the constructed A discrepancy as a new fault in DP-SGD.

## 5. Independent review and stopping rule

A reviewer who did not author the first report checks the source interpretations, original-proof evidence and all four outcomes. The reviewer receives the exact inputs and evidence; this is an exposed review, not a blind experiment. They must challenge at least these failure modes: inferring fault from an instance binder alone; overlooking an independently constructed provider; joining unrelated same-name locals; treating historical extraction as fresh independent replay; extending D to the whole paper.

Record agreement or disagreement per case with evidence. If a judgment requires deeper mathematical interpretation, escalate that bounded question to a stronger reasoning model or human with the exact spans and competing readings. A cheaper executor should continue unrelated evidence collection while that question waits.

Stop after the reviewed finding/control report. If an actual evidence gap blocks a case, record the missing operation and why retained evidence or ordinary Lean cannot resolve it before proposing engineering work. Resource configuration Q.1–Q.3 is not an automatic fallback. No new extraction, corpus, full-paper run or comparative pilot follows from a mere desire for more evidence. M.2/M.3 remain incomplete if their required evidence/review is missing, even if a report file exists.
