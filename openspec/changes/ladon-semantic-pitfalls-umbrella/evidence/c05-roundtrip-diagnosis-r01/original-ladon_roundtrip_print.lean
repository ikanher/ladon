/- Closed proof telescopes need names even when an instance is referenced only
   by later binder types. Some Lean lambda printers omit those names. This local
   delaborator preserves binder kinds and leaves the expression unchanged. -/
open Lean.PrettyPrinter.Delaborator Lean.PrettyPrinter.Delaborator.SubExpr in
private partial def delabRoundtripLambda (maxDepth : Nat)
    (names : NameSet := {}) (depth := 0) : Delab := do
  let e ← getExpr
  if !e.isLambda then return ← delab
  if maxDepth != 0 && depth > maxDepth then
    throwError "closed proof lambda depth exceeds {maxDepth}"
  let type ← withBindingDomain delab
  withBindingBodyUnusedName (avoid := names) fun name => do
    let body ← delabRoundtripLambda maxDepth (names.insert name.getId) (depth + 1)
    let name : TSyntax `ident := ⟨name⟩
    match e.binderInfo with
    | .default => `(fun ($name : $type) => $body)
    | .implicit => `(fun {$name : $type} => $body)
    | .strictImplicit => `(fun ⦃$name : $type⦄ => $body)
    | .instImplicit => `(fun [$name : $type] => $body)

private def roundtripProofText (proof : Expr) (maxDepth : Nat := 64) : MetaM String := do
  let printed ← Lean.PrettyPrinter.ppExprWithInfos proof (delab := delabRoundtripLambda maxDepth)
  pure printed.fmt.pretty
