# Source-aware alias certificate proposal

Mechanism proposal only; no Lean probe or product edit was run. The installed source tree is at `/home/codex/.elan/toolchains/leanprover--lean4---v4.32.1/src/lean`. The shell's default `lean --version` reports 4.35.0, so root should explicitly select 4.32.1 for any later probe.

## Source-context traversal

Recursively navigate the generated proposition value (the same local `info.value` observed by `ladon_prose_observation.lean`). At each `forallE n ty body bi`, invoke `withLocalDecl n bi ty`, recurse on `body.instantiate1 fvar`, and append the returned fvar to an ordered binder array. At each lambda, open it similarly only if the grammar expects a lambda; otherwise reject. Match the chosen expression path while locals are live; capture source and canonical Expr values in this context. Track the ordered full fvar prefix at the target, not just target free variables. `mkForallFVars` defaults `usedOnly := false`, which is required so guards and unused binders survive closure. Preserve every binder's actual BinderInfo and type.

Instance implicits are ordinary forall binders for traversal, but local-instance registration can affect typeclass synthesis. Avoid synthesis inside a scope whose intended instance context is unclear; thread the actual instance context through `withLocalDecl` and check the chosen instance, or build only the exact application from resolved constants/arguments. Never reconstruct a scope from serialized fvar names.

## Bounded head unfolding and equality evidence

A bounded recognizer may repeatedly call `Lean.Meta.unfoldDefinition?` on the expression head (after `getAppFn`/rebuilding with original args), at most 32 times. Stop before unfolding heads `HAdd.hAdd`, `Nat.add`, or the direct supported `n`; require syntactic progress and track visited expressions to reject cycles. This is discovery only: Meta transparency/definitional equality is not certificate authority.

For the order alias, after deriving literal `d` from a permitted selected expression, construct `Nat.add n d` in the live context and ask `mkEqRefl originalOrder`. This creates an Eq.refl proof whose inferred type is `originalOrder = originalOrder`; the kernel accepts it at the desired `originalOrder = Nat.add n d` type only when that RHS is definitionally equal. Infer the proof type and use `isDefEq` only as a preflight, then close proof and expected type over the same exact fvar prefix with `mkForallFVars` (`usedOnly := false`). The checked theorem declaration is the authority. If scoped definitional equality does not hold, return unsupported/residual; do not rewrite the proposition.

For an output coefficient, build the exact selected multiplication expression with the elaborated/typed `HMul.hMul` application and existing coefficient fvar. Likewise obtain only `mkEqRefl originalOutput` and use a checked closed theorem. Avoid `mkAppM` synthesis if it can select a different multiplication instance; retain the selected instance as part of the expression. Literal arithmetic must use bounded Nat evaluation with no guessed coercions.

## Kernel-checking the closed certificate

After closing proof and proposition over all binders, add a fresh theorem declaration using `Lean.Declaration.thmDecl (Lean.mkTheoremValEx name levelParams closedType closedProof [name])`, then the checked `Lean.addDecl` route. In 4.32.1 `TheoremVal` stores `name`, `levelParams`, `type`, `value`, and `all`; `Declaration.thmDecl` is documented as a declaration sent to the kernel. Do not use an unchecked declaration path. Ensure the closed proof contains no free variables or metavariables and its type is the closed Eq proposition. Check the resulting environment contains a theorem declaration under the fresh name; serialize only the closed proposition/proof reference and freshness data needed by the caller.

## Exact 4.32.1 source anchors

- `Lean/Meta/Basic.lean:1142-1148`: `mkForallFVars` / `mkLambdaFVars`, including `usedOnly` default false.
- `Lean/Meta/Basic.lean:1779-1798`: `withLocalDecl` API; instance implications need explicit attention.
- `Lean/Meta/WHNF.lean:871`: `unfoldDefinition?` returns `Option Expr`; this Meta transformation is not proof evidence.
- `Lean/Meta/AppBuilder.lean:84`: `mkEqRefl`; `:364` `mkAppM`.
- `Lean/Declaration.lean:142-147`: `TheoremVal`; `:185-190`: `Declaration.thmDecl`.
- `Lean/AddDecl.lean:22`: `Kernel.Environment.addDecl`; `:227` public `Lean.addDecl` route. Use the checked path, not unchecked internals.

## Main proof-valued risks

1. Equality under the open source context can depend on local instance fvars or reducible local definitions. Reconstructing the operation from names can select another instance.
2. Closing only target free variables drops outer guards and unused quantified binders; closure must use the exact observed binder prefix.
3. The order may be a Nat alias but `HAdd.hAdd` can carry an instance parameter. Require exact expression-level support and kernel acceptance; unsupported forms remain residual.
4. `Eq.refl original` at the desired canonical RHS succeeds only by definitional equality. A `Meta.isDefEq` result alone is not the admitted certificate.
5. `unfoldDefinition?` can use transparency/smart unfolding settings. Bound its iterations and use it for navigation only; kernel theorem checking is the acceptance gate.
6. Literal discovery and number bounds need independent enforcement; no broad normalization or whole-proposition unfolding.
