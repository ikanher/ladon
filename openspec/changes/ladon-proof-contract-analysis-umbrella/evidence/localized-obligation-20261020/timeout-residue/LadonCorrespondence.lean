import Lean
import Lean
import Lean
import Std

namespace ThreeSteps

def N0 (s _x : Nat) : Nat := s
def N1 (s _x : Nat) : Nat := s
def N2 (s _x : Nat) : Nat := s + 2
def N3 (_s _x : Nat) : Nat := 0

def F1 (x : Nat) : Nat := x + 1
def F2 (x : Nat) : Nat := x + 2
def F3 (x : Nat) : Nat := x + 3
def G (x : Nat) : Nat := F2 (F1 x)
def H (x : Nat) : Nat := F3 (G x)
def C : Nat := 1


run_cmd do
  let env ← Lean.getEnv
  if env.contains `ThreeSteps.firstBound then throwError "parent declaration imported"
  if env.header.moduleNames.contains `ThreeSteps then throwError "original source module imported"
theorem _root_.LadonContractPrefix_0792dcae4351e966 : _root_.True := by trivial
run_cmd do
  let count := (← Lean.Elab.Command.getScopes).length - 1
  for _ in List.range count do
    let scope ← Lean.Elab.Command.getScope
    if scope.header.isEmpty then
      Lean.Elab.Command.elabCommand (← `(command| end))
    else
      Lean.Elab.Command.elabCommand (← `(command| end $(Lean.mkIdent (Lean.Name.mkSimple scope.header))))

run_cmd do
  let env ← Lean.getEnv
  if env.contains `ThreeSteps.endpoint then throwError "parent declaration imported"
  if env.header.moduleNames.contains `ThreeSteps then throwError "original source module imported"
theorem _root_.LadonContractPrefix_090b5c1adeaca143 : _root_.True := by trivial
run_cmd do
  let count := (← Lean.Elab.Command.getScopes).length - 1
  for _ in List.range count do
    let scope ← Lean.Elab.Command.getScope
    if scope.header.isEmpty then
      Lean.Elab.Command.elabCommand (← `(command| end))
    else
      Lean.Elab.Command.elabCommand (← `(command| end $(Lean.mkIdent (Lean.Name.mkSimple scope.header))))

run_cmd Lean.Elab.Command.modifyScope (fun scope => { header := scope.header, opts := Lean.internal.cmdlineSnapshots.set (Lean.Elab.async.set {} false) true })
set_option autoImplicit false
-- Composed in the exact generated source context after its command scope reset.
open Lean Elab Command Meta
/- Complete structural expression serialization with explicit subtree sharing.
   ExprStructEq is essential: Expr's ordinary BEq ignores binder annotations. -/
private structure ExprGraphState where
  seen : ExprStructMap Nat := {}
  nodes : Array Json := #[]

private partial def encodeExprNode (expr : Expr) : StateM ExprGraphState Nat := do
  let before : ExprGraphState ← get
  if let some id := before.seen[ExprStructEq.mk expr]? then return id
  let node ← match expr with
    | .bvar index => pure (Json.arr #[toJson "bvar", toJson index])
    | .fvar id => pure (Json.arr #[toJson "fvar", toJson (repr id.name).pretty])
    | .mvar id => pure (Json.arr #[toJson "mvar", toJson (repr id.name).pretty])
    | .sort level => pure (Json.arr #[toJson "sort", toJson (repr level).pretty])
    | .const name levels => pure (Json.arr #[toJson "const", toJson (repr name).pretty, toJson (repr levels).pretty])
    | .app fn arg => do
        let f ← encodeExprNode fn
        let a ← encodeExprNode arg
        pure (Json.arr #[toJson "app", toJson f, toJson a])
    | .lam name type body info | .forallE name type body info => do
        let t ← encodeExprNode type
        let b ← encodeExprNode body
        let tag := if expr.isLambda then "lam" else "forallE"
        pure (Json.arr #[toJson tag, toJson (repr name).pretty, toJson (repr info).pretty, toJson t, toJson b])
    | .letE name type value body nondep => do
        let t ← encodeExprNode type
        let v ← encodeExprNode value
        let b ← encodeExprNode body
        pure (Json.arr #[toJson "letE", toJson (repr name).pretty, toJson nondep, toJson t, toJson v, toJson b])
    | .lit value => pure (Json.arr #[toJson "lit", toJson (repr value).pretty])
    | .mdata data body => do
        let b ← encodeExprNode body
        pure (Json.arr #[toJson "mdata", toJson (repr data).pretty, toJson b])
    | .proj name index body => do
        let b ← encodeExprNode body
        pure (Json.arr #[toJson "proj", toJson (repr name).pretty, toJson index, toJson b])
  let state : ExprGraphState ← get
  let id := state.nodes.size
  set ({ seen := state.seen.insert (ExprStructEq.mk expr) id, nodes := state.nodes.push node } : ExprGraphState)
  return id

private def structuralText (expr : Expr) : String := Id.run do
  let (root, state) := (encodeExprNode expr).run {}
  return "ladon-expr-dag-v1:" ++ Json.compress (Json.mkObj [
    ("root", toJson root), ("nodes", toJson state.nodes)])


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
#check (Nat.add : Nat → Nat → Nat)
#check (ThreeSteps.C : Nat)
#check (ThreeSteps.N0 : Nat → Nat → Nat)
#check (ThreeSteps.H : Nat → Nat)
#check (Nat.mul : Nat → Nat → Nat)
#check (ThreeSteps.N3 : Nat → Nat → Nat)
#check (Fin.val : Fin 5 → Nat)
#check (Nat.add : Nat → Nat → Nat)
#check (ThreeSteps.C : Nat)
#check (ThreeSteps.N0 : Nat → Nat → Nat)
#check (ThreeSteps.F1 : Nat → Nat)
#check (Nat.mul : Nat → Nat → Nat)
#check (ThreeSteps.N1 : Nat → Nat → Nat)
#check (Fin.val : Fin 5 → Nat)
#check (Nat.add : Nat → Nat → Nat)
#check (ThreeSteps.C : Nat)
#check (ThreeSteps.N0 : Nat → Nat → Nat)
#check (ThreeSteps.H : Nat → Nat)
#check (Nat.mul : Nat → Nat → Nat)
#check (ThreeSteps.N3 : Nat → Nat → Nat)
#check (Nat.add : Nat → Nat → Nat)
#check (ThreeSteps.C : Nat)
#check (ThreeSteps.N0 : Nat → Nat → Nat)
#check (ThreeSteps.F1 : Nat → Nat)
#check (Nat.mul : Nat → Nat → Nat)
#check (ThreeSteps.N1 : Nat → Nat → Nat)
#ladon_typed_subject ((∀ (v0 : Nat), (∀ (v1 : Fin 5), (((_root_.ThreeSteps.N1 : Nat → Nat → Nat) v0 ((_root_.ThreeSteps.F1 : Nat → Nat) ((_root_.Fin.val : Fin 5 → Nat) v1))) ≤ ((_root_.Nat.mul : Nat → Nat → Nat) (_root_.ThreeSteps.C : Nat) ((_root_.ThreeSteps.N0 : Nat → Nat → Nat) ((_root_.Nat.add : Nat → Nat → Nat) v0 0) ((_root_.Fin.val : Fin 5 → Nat) v1)))))))

example : (∀ (v0 : Nat), (∀ (v1 : Fin 5), (((_root_.ThreeSteps.N1 : Nat → Nat → Nat) v0 ((_root_.ThreeSteps.F1 : Nat → Nat) ((_root_.Fin.val : Fin 5 → Nat) v1))) ≤ ((_root_.Nat.mul : Nat → Nat → Nat) (_root_.ThreeSteps.C : Nat) ((_root_.ThreeSteps.N0 : Nat → Nat → Nat) ((_root_.Nat.add : Nat → Nat → Nat) v0 0) ((_root_.Fin.val : Fin 5 → Nat) v1)))))) := by
  skip
