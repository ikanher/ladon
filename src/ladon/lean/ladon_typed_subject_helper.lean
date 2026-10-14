-- Composed in the exact generated source context after its command scope reset.
open Lean Elab Command Meta
-- LADON_EXPR_GRAPH

private def ladonSubjectExpr (e : Expr) : MetaM Json := do
  let display ← withOptions (fun o => o.setBool `pp.all true |>.setBool `pp.explicit true
    |>.setBool `pp.fullNames true |>.setBool `pp.notation false) do
    pure (← ppExpr e).pretty
  let result := Json.mkObj [("display", toJson display), ("structural", toJson (structuralText e))]
  if result.compress.utf8ByteSize > 1048576 then throwError "typed expression exceeds 1 MiB"
  return result

private partial def ladonSubjectApplications (e : Expr) (count : IO.Ref Nat)
    (depth : Nat := 0) : MetaM (Array Json) := do
  let visited ← count.get
  if visited >= 4096 || depth > 64 then throwError "typed subject exceeds node/depth bounds"
  count.set (visited + 1)
  match e with
  | .app .. =>
    let args := e.getAppArgs
    let mut rows := #[]
    let mut typedArgs := #[]
    for arg in args do
      typedArgs := typedArgs.push <| Json.mkObj [
        ("expression", ← ladonSubjectExpr arg), ("type", ← ladonSubjectExpr (← inferType arg))]
      rows := rows ++ (← ladonSubjectApplications arg count (depth + 1))
    let head := e.getAppFn
    rows := rows.push <| Json.mkObj [
      ("expression", ← ladonSubjectExpr e), ("resultType", ← ladonSubjectExpr (← inferType e)),
      ("operator", ← ladonSubjectExpr head), ("operatorType", ← ladonSubjectExpr (← inferType head)),
      ("arguments", Json.arr typedArgs)]
    return rows
  | .forallE name type body bi | .lam name type body bi =>
    let rows ← ladonSubjectApplications type count (depth + 1)
    withLocalDecl name bi type fun fvar => do
      return rows ++ (← ladonSubjectApplications (body.instantiate1 fvar) count (depth + 1))
  | .letE name type value body _ =>
    let rows ← ladonSubjectApplications value count (depth + 1)
    withLetDecl name type value fun fvar => do
      return rows ++ (← ladonSubjectApplications (body.instantiate1 fvar) count (depth + 1))
  | .mdata _ body | .proj _ _ body => ladonSubjectApplications body count (depth + 1)
  | _ => return #[]

elab "#ladon_typed_subject " subject:term : command => do
  liftTermElabM do
    let expr ← Term.elabTermEnsuringType subject (some (mkSort .zero)) (catchExPostpone := false)
    Term.synthesizeSyntheticMVarsNoPostponing
    let expr ← instantiateMVars expr
    if expr.hasExprMVar || expr.hasLevelMVar || expr.hasFVar then
      throwError "typed subject is not closed"
    let count ← IO.mkRef 0
    let output := Json.mkObj [
      ("profile", toJson "typed-operators-v2"), ("subject", ← ladonSubjectExpr expr),
      ("type", ← ladonSubjectExpr (← inferType expr)),
      ("applications", Json.arr (← ladonSubjectApplications expr count))]
    let frame := "LADON_TYPED_SUBJECT " ++ output.compress
    if frame.utf8ByteSize > 8388608 then throwError "typed subject exceeds 8 MiB"
    logInfo frame
