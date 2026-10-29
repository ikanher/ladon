# Final sidecar audit

## Reviewed claim

`CoordinateNormBridge.lean` proves the generic implication from coordinate-tuple bounds for a continuous `n`-linear map to its operator norm bound `d^n C`, under exact coordinate expansion and the pointwise coefficient estimate `‖coord x k‖ ≤ ‖x‖`. It specializes this to the product max norm on `Plane = ℝ × ℝ`, where the coordinate vectors have norm one and both coordinate maps satisfy that estimate. The prefix conversion uses `2^n C`; the reverse operator-to-coordinate conversion has factor one. The file also relates coordinate words to evaluations of `iteratedFDeriv`, handles order zero, exhibits a factor-one counterexample, and transports the existing five-order inverse estimate to coordinate bounds.

## Independent audit findings

The generic proof's quantifiers and constants are coherent. Expanding each of the `n` inputs gives a finite sum indexed by `Fin n → Fin d`; each summand is bounded by `C` times the product of input norms, because every coordinate coefficient is bounded by its input norm. The number of summands is `d^n`. The nonnegative hypothesis on `C` supports the multiplication steps. The proof does not need linearity of `coord`: exact expansion and the stated pointwise bounds suffice. The conclusion also covers `n = 0`: the empty tuple index set has one element, `d^0 = 1`, and `iteratedFDeriv` order zero evaluates to the function value. The same argument is well-defined for `d = 0`.

On `Plane`, the product norm is `max ‖x.1‖ ‖x.2‖`; the coordinate vectors have norm one and each coordinate is bounded by that max. Therefore `2^j C ≤ 2^n C` for `j ≤ n` and `C ≥ 0`, yielding the stated prefix constant. The proof of `factor_one_is_false` uses the functional `(x,y) ↦ x+y`: its two coordinate evaluations have absolute value one, while its operator norm under this product max norm is at least two, witnessed at `(1,1)`. This is a valid checked negative control for the converse of the coordinate-to-operator implication.

`coordinateWord_eq` follows the first-slot recursion for iterated Fréchet derivatives, so the slot order is explicit and consistent. `coordinate_inverse_five` first converts the input coordinate prefix bound to the full Fréchet bound with factor `2^(n+5)`, applies the existing five-order theorem, then converts the output back with factor one. Its resulting multiplier `K * 2^(n+5)` is independent of `F` and `C` (though it may depend on order and direction through `K`). No four-order result is asserted.

## Evidence examined

- `.codex/state/coordinate-norm-bridge/CoordinateNormBridge.lean`
- `.codex/state/coordinate-norm-bridge/attempt-6-process.json` (return code 0; axiom reports list only `propext`, `Classical.choice`, and `Quot.sound` for the displayed declarations)
- `.codex/state/coordinate-norm-bridge/attempt-6.lean` (`cmp` confirms it is byte-identical to `CoordinateNormBridge.lean`)
- `.codex/state/coordinate-norm-bridge/FreshSourceBridge.lean` and `fresh-source-process.json` (recorded return code 0 with the same displayed axiom set)
- `.codex/state/coordinate-norm-bridge/CONTRACT.md`
- Earlier source-pair `REPORT.md` and `ParameterFreeBridge.lean`

The only commands used for this final review were read-only `sed`, `rg`, `cat`, `ls`, `cmp`, and the board `read` command. I did not invoke Lean, run a build, or edit source/runtime/dependency files. This audit file is the only written artifact.

## Limitations and trust boundary

This is a source-level independent review of the sidecar proof and recorded receipts; I did not independently replay the compiler. The receipts establish compilation of the submitted files against their recorded library roots, not a fresh build of those dependencies. The bridge formalizes a chosen full-Fréchet versus coordinate-partial convention on the product max norm. It does not identify the paper's unspecified `C_y^m` norm, settle its scalar or torus conventions, establish source fidelity beyond the attributed reading, prove existence or uniqueness, or prove the four-order estimate. The inverse transport is a specialization of the existing five-order formal theorem, not independent evidence for the paper's norm convention or a refutation of the paper.
