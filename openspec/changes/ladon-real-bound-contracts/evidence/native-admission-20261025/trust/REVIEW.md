# Real native admission trust review (assignment 1647)

## Scope and evidence

Read-only inspection of `src/ladon/real_bound_shape.py`, `_real_bound_terms.py`, `real_bound_binding.py`, `real_bound_binding_check.py`, `real_bound_admission_check.py`, and Lean bridges `lean/LadonRealBoundBinding.lean`, `lean/LadonRealBound.lean`, `lean/LadonRealBoundDerivative.lean`; inspected `tests/test_real_bound_shape.py`. No builds, Lean checks, database edits, or canonical source/test edits.

## Finding: scalar operations are syntax-shaped, not instance-bound

`_real_bound_terms.is_nonnegative` checks `LE.le` and `OfNat.ofNat`, Real type arguments, literal zero, and the final binder, but ignores the order and OfNat instance arguments (`args[1]`, `zero_args[2]`). `real_bound_shape._guards` similarly checks `HMul.hMul` and Real type arguments and operands, while ignoring its multiplication instance (`args[3]`). Thus observed JSON can describe a Real proposition whose actual typeclass dictionary is noncanonical. The source-local statement's dictionaries are faithfully carried by the exact observed Expr and the fresh `ladon_bound_admission%` proves laws for that proposition, but those laws alone do not establish canonical Real order/multiplication semantics. The derivative adapter does synthesize `jointDerivativeMeasure` under source-owned instances; this does not discharge the separate scalar semantics issue.

Minimal red syntax controls: mutate the order dictionary in `LE.le` to a distinct constant; mutate the zero `OfNat` dictionary; mutate `HMul.hMul` dictionary. Each must leave candidate null or carry a non-admissible scalar profile. Build a real Lean fixture with a local/scoped replacement `LE Real`, `OfNat Real`, and `HMul Real Real Real` that makes comparisons/products degenerate, then show prefix-law acceptance is insufficient absent a canonical dictionary guard. For admission, compare `inferType`'s actual scalar dictionary Exprs by definitional equality against canonical Real instances resolved in a clean trusted module; reject local overrides even if a saved receipt says passed.

## Evidence/native trust contract recommendation

Use a closed `real-bound-v1` payload nested in existing `proofir.contract`, with profile digest and typed record bound to the exact observed source snapshot, normalized expression identity, source bytes, pinned toolchain/environment, admission-plan identity, checker/binding/helper/import identities, and fresh run receipt. On create, recompute all identities and run J plus scalar-law checks now; never accept caller booleans, embedded result JSON, or matching old hashes as fresh admission. Exact evidence references must resolve to immutable, content-addressed check-run/source records and be owned by this artifact; reject duplicate/substituted refs and unknown fields. Offline validation/storage/report must lower authority to an explicit historical state and cannot issue fresh evidence. Replay must reopen exact source/helper/import set, regenerate plan, check profile compatibility and prove all freshness hashes before running.

Red tests: forged `status=passed` and receipt; old receipt with changed source; helper/import digest mismatch; plan/source/profile mismatch; replace evidence ref with another valid run; duplicate reference; wrong owner; missing scalar-check run; weak/missing bound guard; each scalar dictionary substitution; unknown Real payload key; unknown variant/profile version. Assert invalid evidence blocks fresh creation and historical offline inspection remains visibly historical, with `contract=null`/no activation.

## Limitations

This is a static adversarial review; no Lean counterfeit fixture or fresh replay was run. The exact saved-evidence and native storage implementation does not yet exist on this frontier, so the recommendations specify gates rather than certify an implementation. Existing derivative prefix evidence proves only its bounded prefix law, not paper norm semantics or Real scalar canonicality.
