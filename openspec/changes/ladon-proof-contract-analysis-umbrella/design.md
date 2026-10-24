# Design

## Context

See proposal.md. Ladon already provides source-bound typed interpretations, exact local-context transport, checked correspondence obligations, a bounded structural AND/OR solver, rational witness checking, and immutable investigation findings. It does not yet compute a mathematical contract frontier across proof routes. Existing outstanding ProofIR and correspondence changes retain their own tasks; this umbrella does not close them by analogy.

Quux sources inspected for this plan are recorded in sources.md. Its propagation algebra has ordered predecessor edges; its antichain consumer is a finite diamond example; its probe separator is a symmetric-matrix example. These are architectural evidence, not an implemented general proof auditor.

## Goals / Non-Goals

**Goals:** discover useful local comparison obligations through a small, soundly interpreted contract fragment; preserve alternative proofs; give LLM callers an executable next step; measure discovery separately from interpretation and propagation.

**Non-Goals:** a complete abstract interpretation of Lean, an automatic NLP semantic oracle, universal proof equivalence, generic cyclic proof acceptance, mandatory Quux dependency, or a promise to find a particular known paper issue. No diagnosis or targeted lemma selection enters a blind handoff.

## Decisions

### Development direction after the big-picture review

Continue the existing implementation and acceptance gates without promising a particular paper diagnosis. First qualify the integrated consumers (task 3.1), then prioritize the independently sourced statement-pair connection (2.1) before expanding the analysis domain. Record the precise limiting feature if that connection remains unsupported; a failed bounded route does not establish general impossibility. Continue the planned refinement child (2.3), then complete repository qualification (3.2) against the resulting implementation.

Evaluate supplied-contract analysis, source production and unfamiliar-source discovery in the existing child protocol's order and under its frozen promotion rules. The preserved no-beam comparison checks legacy behavior and does not exercise the new contract-analysis path. Beam search or another broad paper run needs evidence from the relevant evaluation gates; neither substitutes for source-fidelity review. A later known-target regression must remain separate from unfamiliar-source benefit.

The authoritative current progress and next action live in [tasks.md](tasks.md); measured results remain in their linked evidence packets. Completed infrastructure may coexist with an unmet discovery gate. Preserve historical inputs, first reports and handoffs as the reachable scope becomes clearer.

### Child ownership and order

| Child | Owns | Prerequisites |
|---|---|---|
| [domain](../ladon-proof-contract-domain/design.md) | Contract denotation, dominance, rule admission, native payloads | Existing native v3 identity/authority |
| [producers](../ladon-proof-contract-producers/design.md) | Independent prose and Lean contract production | domain |
| [propagation](../ladon-proof-contract-propagation/design.md) | Bounded AND/OR contract frontiers | domain; producers for real-source integration |
| [bidirectional](../ladon-proof-contract-bidirectional/design.md) | Backward obligations and discrepancy localization | domain, producers, propagation |
| [probes](../archive/2026-10-19-ladon-proof-contract-probes/design.md) | Exact distinguishing application probes | domain, producers, bidirectional |
| [refinement](../ladon-proof-contract-refinement/design.md) | Countermodel lifting and immutable refinement | domain, producers, bidirectional, probes |
| [evaluation](../ladon-proof-contract-evaluation/design.md) | Frozen benchmarks, comparison and discovery decision | All functional children for execution |

Evaluation protocol/custody preparation begins before implementation; held-out contents remain inaccessible to implementers. Domain first admits the shared schema, then producers and propagation can proceed independently against its fixtures. The umbrella owns final CLI composition, finding projection, documentation and integrated compatibility verification. Children own their algorithms and focused tests. Each child is a real OpenSpec packet with its own acceptance contract.

### One contract layer, separate evidence

Keep original statements and interpreted formulas authoritative for their respective subjects. Abstract features are derived summaries with scope, supporting observations and completeness. A structural mismatch is a candidate discrepancy; a checked bridge establishes support; only a checked counterexample to the exact interpreted proposition establishes its falsity. Fidelity to the original prose remains independently reviewed. A difference between proof methods remains visible even if another route establishes the same endpoint.

Use two new closed native kinds, owned by domain: proofir.contract and proofir.contract-analysis. Analysis payloads have closed, versioned variants for propagation, obligation planning, probing and refinement. Reuse source-map, interpretation, correspondence, check-run and attempt-log artifacts. Do not put mathematical semantics in unchecked extension dictionaries.

### Public workflow

Add an opt-in investigation contract command group with produce, propagate, obligations, probe, refine and inspect operations, plus audit for bounded orchestration. Names are proposed public contracts to freeze during implementation; all operations consume immutable artifact/plan paths and write a new destination. Stage commands remain usable independently when later stages are unsupported. The audit driver records source selection and interpreted candidates before formal matching and obeys one shared deadline; it cannot repair or silently select the prose reading that happens to match Lean.

Attach analysis findings to the existing observation/review/report workflow with explicit artifact references. Reviewed contract discrepancies must survive final reports even when the main claim list is empty. Existing progress receipts retain their original reader/projection; any new receipt projection is versioned rather than retroactively modifying old bytes.

### Bounds and stopping

Default analysis bounds: 4096 graph references, 8192 evaluated steps, 64 depth, 128 frontier contracts per statement, 4096 attempted combinations per step, 64 probes, 256 witness candidates, 32 reductions per witness, and 4 refinement rounds. Native 8 MiB artifact/32 MiB batch limits remain. Share one 90-minute audit clock by default; explicit shorter deadlines are honored. Worker RSS uses the shared 12 GiB default and existing stop-and-report diagnostic. A bound produces partial coverage and a named residual; no automatic memory increase or clock reset. Pure graph stages enforce finite work limits as well as deadline polling.

### Validation strategy

Run the small mathematical feasibility gates before broad source integration. Child acceptance includes Lean-backed positive/negative controls, independently enumerated graph oracles, and source/identity mutations. Evaluation has three distinct tracks and a predeclared promotion decision. Infrastructure completion can coexist with a negative discovery result; the umbrella's detection-benefit gate must then remain unmet.

## Risks / Trade-offs

- Contract arithmetic is too crude → begin with a typed nested norm-scale fragment and require checked transfer rules; keep unsupported terms opaque.
- Antichains grow exponentially → preserve witnesses within fixed caps and explicitly report omitted work. Never synthesize a componentwise optimum.
- Both source interpreters repeat the same mistake → freeze prose interpretations before formal matching and use independent fidelity review.
- A second evidence framework duplicates Ladon → use native artifacts and existing checks; introduce only mathematical summaries and new analysis variants.
- A promising abstraction cannot support a real consumer → domain feasibility must check one sequential estimate and one alternative-route trade-off within a 60-minute run, 12 GiB worker cap and existing artifact bounds. Stop expansion if sound composition or bridge representation cannot be demonstrated; record the limiting obligation.
- Evaluation becomes answer-informed → separate development, hidden-answer adjudication and fresh auditor inputs; known target material remains development evidence only.

## Migration Plan

Add opt-in commands and registered kinds; preserve existing structural queries and investigation versions. Existing artifacts retain canonical identities. Unsupported consumers reject new kinds explicitly, including Rust until exercised parity is implemented. Rollback disables new producers/commands while retaining emitted artifacts for later compatible readers. Preserve all prior retest inputs, findings and handoffs; any later experiment gets a newly frozen directory. Planning and implementation never push code.

