# An exercised ordinary-file audit

Preserve the disputed passage before writing a proof. The [frozen inventory](source-inventory.json) records the original version, precise questions, local obligations and proposed controls. Each case below was carried through these steps by the root agent with full knowledge of the paper's diagnosis. This is a usable development recipe, not a blind fidelity detector.

1. Name the exact assertion being questioned, and its assumptions and objects. Keep an interpretation separate from the source sentence.
2. Check that local assertion, not only the final theorem. Use a named Lean declaration where possible, preserving the original context. Record a failed attempt as unsuccessful unless a separate witness establishes falsity.
3. Read the actual proof route for strategy claims. An axiom list or dependency graph does not describe the mathematical argument.
4. Propose a small correction. State whether it changes the argument, narrows the statement, or merely corrects the coverage claim. Check the corrected local obligation separately.
5. Keep original and proposed revisions separate; give a reader reachable support. Adoption remains the mathematical author's decision.

## Polynomial walkthrough

[Original](sources/paper/NavierStokes_LostInTranslation_ArXiv.tex), `ex:example1`, asserts `p x = (x-1)*(x+1)^2` and nonnegativity of that product for real `x ≥ -1`. [Attempted local check](runs/polynomial-wrong-step-01/PolynomialWrongStep.lean) leaves the unequal normal forms in [output](runs/polynomial-wrong-step-01/stdout.txt). That failed tactic alone is not a counterexample. The independent named declarations `wrong_factorization_at_zero` and `wrong_product_negative_at_zero` in [Polynomial.lean](cases/Polynomial.lean) give the actual witnesses at `x=0`.

The faithful control `corrected_factorization` uses `(x+1)*(x-1)^2`. `original_conclusion` preserves exactly `x : ℝ`, `hx : -1 ≤ x`, and `0 ≤ p x`. It checks without adopting the false intermediate identity. The [policy output](runs/polynomial-01/stdout.txt) concerns all four printed declarations, not fidelity of an entire manuscript.

## Least-element walkthrough

[Original](sources/paper/NavierStokes_LostInTranslation_ArXiv.tex), `sec:why`, displays a concrete `p_e` and total definitions `n_e`, `r_e`. [LeastElement.lean](cases/LeastElement.lean) preserves those definitions and the final ring identity in a namespace. Its additional declarations separately prove a root `(n,0)` for every natural `n`, `¬ B_e n`, the empty set, and the resulting defaults `n_e=0`, `r_e=1`.

The Boolean `!=` in the supplied code is preserved: its coercion is a proposition that the Boolean value is true. The successful [second attempt](runs/least-element-02/stdout.txt) simplifies that assertion at the root. It does not silently replace the predicate. `conditional_least` and `conditional_algebra` use `S : Set ℕ`, `hS : S.Nonempty`; adding this hypothesis narrows the claim and does not repair existence for the concrete empty set. The algebra itself remains correct.

## Matrix walkthrough

[Original](sources/paper/NavierStokes_LostInTranslation_ArXiv.tex), `ex:example2`, uses an orthonormal eigenbasis and trace invariance. [Matrix.lean](cases/Matrix.lean) checks two reconstructed declarations with the same proposition: `A : Matrix n n ℝ`, finite index type, `Aᵀ=A`, and `0 ≤ trace (A*A)`.

`direct` expands the trace and uses symmetry. `diagonalization` calls the actual Mathlib spectral theorem, conjugates the square, uses trace invariance, and sums diagonal squares. The [accepted output](runs/matrix-02/stdout.txt) validates both declarations under the permitted axioms. Reading these explicit proof steps supports the root's method judgment: the direct route is valid but does not validate the omitted eigenbasis step. The faithful spectral control receives no false-proof finding.

## Replay

From the Ladon repository root, with the [fixture prepared](environment/README.md):

```bash
uv run python openspec/changes/ladon-proof-correspondence-audit-umbrella/evidence/r70/replay.py new-polynomial openspec/changes/ladon-proof-correspondence-audit-umbrella/evidence/r70/cases/Polynomial.lean
uv run python openspec/changes/ladon-proof-correspondence-audit-umbrella/evidence/r70/replay.py new-least openspec/changes/ladon-proof-correspondence-audit-umbrella/evidence/r70/cases/LeastElement.lean
uv run python openspec/changes/ladon-proof-correspondence-audit-umbrella/evidence/r70/replay.py new-matrix openspec/changes/ladon-proof-correspondence-audit-umbrella/evidence/r70/cases/Matrix.lean
```

Use a fresh run ID: recorded attempts are never overwritten. The thin [replay script](replay.py) calls the existing supervisor; the actual mathematical command is `lake env lean ABSOLUTE_SOURCE_PATH` in the isolated fixture. Inspect exit status **and** every expected `#print axioms` result. Accept only the expected named declarations with permitted axioms `{propext, Classical.choice, Quot.sound}` and no `sorryAx` or other axiom. The script records observations; it is not an automatic correspondence verdict or canonical proof receipt.

Existing Ladon claim/guide/assessment companions were not needed to settle these small local questions. Creating them would add reconstruction without helping this consumer. Source-goal completion remains an optional route when an application must be bound to a captured source goal: [existing documentation](../../../../../docs/SOURCE_GOAL_COMPLETION.md). Its correct `proof-search goal complete` help was exercised on the frozen source candidate: [command record](cli/complete-help.record.json), [output](cli/complete-help.stdout). No mathematical completion operation was run, and no installed qualification was renewed.
