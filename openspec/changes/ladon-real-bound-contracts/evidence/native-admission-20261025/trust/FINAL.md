# Assignment 1647 final: Real-native trust boundary audit

## Outcome

Static audit found a concrete admission gap that must be closed before `real-bound-v1` can be considered semantically admitted: the observed syntax parser recognizes Real operations by head/type/operands, but does not bind their typeclass dictionaries to canonical Real instances. The live Lean bridge faithfully checks the exact observed proposition, so fresh checking by itself cannot repair this gap.

## Findings and evidence

- `src/ladon/_real_bound_terms.py:is_nonnegative` ignores the `LE.le` order dictionary and `OfNat.ofNat` dictionary.
- `src/ladon/real_bound_shape.py:_guards` ignores the `HMul.hMul` dictionary.
- `src/ladon/lean/LadonRealBoundBinding.lean:observedBoundLaw` compares the full live normalized Expr with the observed JSON and derives prefix laws for that source proposition. This is a strong source-binding boundary, but does not require canonical Real scalar instances.
- `src/ladon/lean/LadonRealBoundDerivative.lean` resolves `jointDerivativeMeasure` using source-owned instances. That establishes the adapter's joint derivative measure shape, not canonical multiplication/order semantics in the observed scalar statements.
- `src/ladon/real_bound_binding_check.py` regenerates the plan, checks source/environment freshness, and verifies checker identity before/after execution. Existing fixed derivative evidence is therefore not enough to bypass a new scalar admission gate.

Minimal red controls are recorded in `.codex/state/real-native/trust/REVIEW.md`: mutate each of the order, zero, and multiplication dictionaries in the observed expression; require candidate rejection or explicit unresolved scalar semantics. A Lean counterfeit fixture should establish a proposition under replacement Real instances and show that `Admission` alone is insufficient. The positive path should compare the actual dictionary Exprs to canonical instances from a clean trusted module.

## Native provenance recommendation

Keep the new profile as a closed variant inside `proofir.contract` and preserve old artifact identifiers, but route it through a distinct validator/dispatcher. Existing `proof_contracts.validate_contract` explicitly accepts only `norm-scale-v1`; existing payload validation, comparison recomputation and propagation consumers consume that old record schema. A Real payload must not pass through these paths by duck typing or shared fields. Until task 3.2, all comparison/propagation/obligation/route consumers should reject Real profile inputs.

A fresh Real contract should bind its closed typed record to exact statement/source-map refs, source bytes and environment, generated plan, profile digest, helper/import/checker identities, and fresh check-run evidence. Resolve refs against exact owning artifacts/content identities; reject substituted, duplicate, stale, or wrong-owner refs. Creation must recalculate identities and execute J plus canonical scalar checks. Offline validation/storage/report may display the saved result only as explicitly historical and must not create fresh evidence or activate a contract. Replay must regenerate the plan from reopened source and recheck freshness before execution.

Red cases should include forged pass flags/receipt, changed source, changed helper or imported module, profile/plan mismatch, evidence substitution/duplicate/wrong owner, missing scalar check, each noncanonical dictionary, weakened guards, extra payload keys, and unknown profile versions. Invalid or historical-only evidence must yield no active contract.

## Peer challenge and limitation

I challenged `real_native_consumers_a` on dispatch and evidence ownership (#1653). Their independent inventory confirms old consumers are closed/profile-gated, lists `_contract_propagation_inputs.read_contracts`, comparison/propagation recomputation and obligation/probe/provider/context/route bridges as explicit rejection gates, and reports existing SQLite `proofir_v3_contracts.record_json/profile_digest` storage can hold the closed record without a new kind/table. They also confirm typed statement/source-map/check-run refs and exact batch owner resolution are the appropriate evidence path. No contradiction to the scalar dictionary finding was identified.

This assignment was static only: no Lean counterfeit fixture, tests, builds, SQLite mutation, or source edits were performed. This is a gate recommendation, not certification of a not-yet-implemented Real native variant.
