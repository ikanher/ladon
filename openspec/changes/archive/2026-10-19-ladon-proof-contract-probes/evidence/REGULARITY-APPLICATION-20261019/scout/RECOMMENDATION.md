# Application-probe consumer scout

Status: read-only implementation scout for task 1.1 after accepted finite calibration. No tests, Lean, builds, source/OpenSpec/frozen edits, or source-pair reads were performed.

## Recommendation

Use the native correspondence as the source-bound input to one new `probes` analysis stage. Do not build a classifier over `norm-scale-v1` summary fields. Those fields can select a candidate template or reject an unsupported source shape; the exact propositions must come from two owner-validated `proofir.interpretation` records and their deterministically lowered formulas, tied to freshly rebuilt correspondence/application contexts.

The smallest useful first slice is `regularity-boundary-v1`. Start with a real source-derived `proofir.contract` pair and two exact correspondence owners whose `sliceId`, source selection/digest, environment, and object map agree. Their `interpretationRef`s resolve to source-map-anchored formulas P and Q. The worker rebuilds both correspondences from the native batch (not stored goal strings), checks the selected source application and strict parent-free prefix under the shared absolute deadline, then derives the direction-specific goal from the actual lowered formulas and shared mapped context. Keep one direction per attempt. Check P → Q and Q → P as separate attempts. A counterexample row must be a generated exact application goal under the selected map, or an existential witness goal whose binders and typed domains are regenerated from the matched interpretations. If the template cannot derive that exact witness/context, keep the row unresolved; do not infer non-implication from a failed implication proof. Semantic separation requires Lean completion, accepted replay, and accepted trust for that exact goal. Failed elaboration/search/timeout is unresolved. If the pair cannot be joined on the exact same selected context and map, emit `unsupported-context-pair` and stop before Lean.

A closed request can extend the current context-bridge envelope:

```json
{
  "repoRoot": "...",
  "context": {"artifacts": ["complete native ProofIR batch"]},
  "left": {"contractRef": {"artifactRef": "sha256:...", "kind": "contract", "localId": "..."}, "correspondenceRef": {"artifactRef": "sha256:...", "kind": "correspondence", "localId": "..."}},
  "right": {"contractRef": {"artifactRef": "sha256:...", "kind": "contract", "localId": "..."}, "correspondenceRef": {"artifactRef": "sha256:...", "kind": "correspondence", "localId": "..."}},
  "selector": {"familyId": "regularity-boundary", "templateVersion": "regularity-boundary-v1", "featureId": "regularity.offset", "direction": "left-to-right", "observation": "implication"},
  "deadlineMonotonic": "one inherited absolute monotonic deadline",
  "limits": {"timeout_seconds": 30, "max_rss_bytes": 12884901888, "max_output_bytes": 8388608}
}
```

All identifiers above are exact references or closed enum values, not user-authored formulas, maps, or goal text. The actual stored request must keep the existing 30-second / 12-GiB / 8-MiB hard ceilings. A `counterexample` observation can select only the opposite closed generated template; it cannot attach an arbitrary formula. Exact refs are resolved from the validated batch, and each contract must be tied to the corresponding interpretation source map by a unique source-map owner. Require equal `environmentRef`; for the first version require identical fresh `sliceId`, source selection/digest, and object map. Do not invent a transport if they differ.

The worker should factor/reuse `_native_plan` and the preparation sequence in `_proof_contract_context_preparation.py`: validate the native artifact batch; resolve the exact correspondence and interpretation owners; regenerate with `prepare_correspondence`; call `bind_native_interpretation`; compare the regenerated semantic payload; re-extract `selection` with `scoped=True`; confirm source bytes/environment; and run `_prefix`/`check_generated_prefix`. `prepare_context` already performs this for one correspondence and returns the exact `originalInterpretation`, `objectMap`, `originalSliceId`, selection, source, environment, strict-prefix digest, and typed generated goals. For a pair, avoid accepting either saved plan; rebuild both under the same outer deadline and check the pair invariant before constructing any probe goal. Existing `check_context_bridge` demonstrates exact `planId` regeneration and bounded checker terms, but its current goal-id whitelist and result schema need probe-specific closed variants.

The probe result belongs in `proofir.contract-analysis` stage `probes`, with exact left/right contract refs, exact correspondence/interpretation/source-map refs, selector/version/direction, regenerated goal digest, exact context/object-map identity, attempt/check-run refs, and residuals. Extend `validate_analysis_payload` with a closed `probes` validator; validate exact-reference closure, same-environment constraints and recomputation. Do not encode generated claims as `proofir.attempt-log`: that schema requires a derivation step and rule, which a generated implication does not have. Reference a `proofir.check-run` for each actual Lean attempt, and use a separately versioned probe-attempt record for unsupported/unattempted rows. Add opt-in `probe`/`inspect` CLI dispatch only after the payload/rebuild path exists.

## Five selectors and current source-profile fit

Use closed semantic IDs: `regularity-boundary`, `constant-choice-position`, `witness-dependence`, `restricted-domain`, and `inequality-direction`. Each selector names the relevant binder/feature identity from the validated interpretations; template generation inspects the exact AST and refuses a mismatch. The template label never supplies formula semantics.

| Family | Current exact lowering / extraction fit | Recommendation |
| --- | --- | --- |
| Regularity boundary | `proof_contract_recognition` recognizes the specific Nat estimate shape and offset. The general typed interpretation lowerer supports its `forall`, `app`, and `le` nodes. | First slice candidate if two actual interpretations differ only at the identified offset and the matching source context/map is available. Generate from interpretation AST, not the offset summary. |
| Constant before parameter | The contract recognizer can represent one existential estimate coefficient and its position/dependencies, but `_proof_contract_source_obligations_formula._formula_symbols` requires exactly two universal Nat binders and the existing generated bridge constructs a global-coefficient formula. | Do not claim source-goal support through the existing source-obligation bridge. A typed interpretation can express the quantifier order, but this requires the new correspondence-pair planner to lower/check that exact AST. |
| Witness dependence | The recognizer permits at most one existential and requires it to be the estimate coefficient; extra existential binders are rejected. Contract constant/witness summaries are coherent, so a separate free witness family is not independently represented. | Unsupported for a distinct witness today. Do not double-count the coefficient-choice case as both families. |
| Restricted domain | The interpretation type fragment can spell types such as `Fin 2`, but source contract recognition explicitly restricts binder domains to Nat and rejects restricted/Subtype domains. | Unsupported as a native extracted-contract family until the contract profile/source recognizer admits and records the exact domain. |
| Inequality direction | Source recognition requires builtin Nat `LE.le` and a fixed estimate/product layout. The interpretation AST supports `lt`/`le`, but contract extraction does not accept an arbitrary reversed proposition. | Unsupported as a native extracted-contract family under current profile; keep an explicit residual. |

Therefore all five actual source-contract families are not supportable through the existing `norm-scale-v1` extraction/checker path. Only the regularity-offset family is a credible first end-to-end slice now. The general interpretation AST is broader (`forall`, `exists`, `eq`, `lt`, `le`, implications, conjunctions, negation, typed applications), but a source-map anchor is attributed provenance, not proof of fidelity, and it does not widen the source contract profile. Hand-authored interpretations may be useful narrowly for checker plumbing; they must retain `attributed-unreviewed` and cannot stand in for extracted native source contracts or establish source-pair facts.

## Hardest feasibility assumption

The hardest assumption is that two independently owned source interpretations can be freshly rebound to the *same* formal application slice and object map while preserving a well-defined contract-to-interpretation source-map association. Current `prepare_context` handles one interpretation/correspondence, while `proofir.contract` and `proofir.interpretation` are separate owners and the correspondence batch validator checks the interpretation/source-map pair, not semantic fidelity between that interpretation and a contract summary. Require that common-context join explicitly; do not infer it from equal contract feature records. The first gate should measure that join and one exact goal end-to-end inside a single 90-second envelope. If no authentic regularity pair satisfies it, stop and report the unsupported binding rather than manufacture one.

## Source pointers

- `src/ladon/_proof_contract_context_preparation.py`: `_native_plan`, `_owner`, `prepare_context`, fresh slice and parent-free prefix binding.
- `src/ladon/_proof_contract_context_goals.py`: existing goal reconstruction and context binding.
- `src/ladon/correspondence_interpretation.py`: bounded typed formula/domain grammar and lexical scope.
- `src/ladon/proofir_correspondence.py` and `src/ladon/proofir_correspondence_payloads.py`: exact interpretation/source-map/correspondence reference ownership and batch validation.
- `src/ladon/proof_contract_recognition.py`: narrow source-contract estimate recognition; Nat domains, one existential coefficient, fixed inequality/product form.
- `src/ladon/_proof_contract_source_obligations_formula.py`: the present generated source-obligation profile is exactly two universal Nat binders.
- `src/ladon/proof_contract_payloads.py`: `proofir.contract-analysis` currently dispatches `comparison`, `propagation`, and `obligations`; add a closed `probes` variant rather than an unchecked extension.
