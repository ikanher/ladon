# Independent audit: parameter-free bridge and interpretation record

Scope: source review only, following assignment post 1851. No Lean, build, test, network, source, runtime, or dependency changes were performed by this reviewer. The running `run_public_checks.py` process was left undisturbed.

## Bridge

`ParameterFreeBridge.lean` correctly erases the dummy parameter with `eraseParameter : (Fin 0 → ℝ) × Plane ≃ₗᵢ[ℝ] Plane`. Its norm proof reduces the product maximum norm to the plane norm because the unique parameter is zero. `norm_liftSource` uses the linear-isometry composition theorem for `iteratedFDeriv`; this gives exact equality of the *full Fréchet multilinear operator norms* at every order, not just coordinate directional derivatives. `bound_equiv` then proves equivalence between `JetBound ... Set.univ` and the defined prefix bound on every plane point.

The inverse commutation claim is also exact at the definitions used: family `inverse` applies `directionalInverse d` to the Fourier coefficients of each parameter slice, while `planeInverse` applies that same operator to the coefficients of F; after lifting by the zero-dimensional isometry, `lift_inverse` is definitional (`rfl`). `Direction.temporal` has vector `(sqrt 2 - 1, 1)` in the source `TorusInverse.lean`, agreeing with the fixed `vt` in the paper. This checks operator identity at the formal definitions; it does not establish the paper's inverse theorem independently.

`plane_inverse_five` specializes the existing `inverse_finiteJets` theorem and transports its prefix bound through `bound_equiv`. Its assumptions supply smoothness, periodicity, and nonnegative C; it derives an `n+5` to `n` bound with a nonnegative constant chosen independently of F and C. Mean zero is not used by that theorem, so adding it would be a harmless strengthening of the premise. This is only a five-order adapter.

## Interpretation record

The formula in `interpretation-record.json` captures the displayed *estimate* with: fixed temporal direction; smooth and periodic plane function; zero mean input; nonnegative input bound C; nonnegative K chosen per n before F,C; input prefix through n+4; output prefix through n; and coefficient K*C. `TorusJetBound` explicitly quantifies every order `j ≤ n`, so it retains lower as well as top order. The record does not encode the PDE, Fourier formula, or zero-mean output/uniqueness clauses of the whole lemma; its scope should remain “estimate mapping” rather than full Lemma 8.6.

The excerpt does not define `C_y^m`. The Lean record chooses the full Fréchet operator norm on iterated derivatives, which is a coherent convention and is explicitly labeled “chosen ... NOT ... extracted from the paper” in the Lean definition. The source-only readings likewise flag the convention as unstated. No equivalence between this full operator norm and the paper's conventional coordinate C^m norm is proved by this bridge. Keep that mapping unresolved.

## Boundary

The five-order theorem cannot discharge the record's four-order input premise. The current `run_public_checks.py` is attempting the same five-order witness against the four-order goal; its outcome must be reported as a negative completion/adapter result, not as a mathematical refutation of the source claim. The source claim itself is the four-order coordinate-norm statement in (8.19); this adapter neither proves nor refutes it.

No full inverse existence/uniqueness, correctness of the paper, chart/scaling result, or native investigation frontier is established here.
