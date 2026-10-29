import Lean
import Lean.Meta.Transform
import LadonRealBound

namespace Ladon.RealBoundBinding
open Lean Meta Elab Term

private def binderInfoName : BinderInfo → String
  | .default => "explicit"
  | .implicit => "implicit"
  | .strictImplicit => "strict-implicit"
  | .instImplicit => "instance-implicit"

private partial def exprJson : Expr → Json
  | .bvar index => Json.mkObj [("bvar", toJson index)]
  | .fvar id => Json.mkObj [("fvar", toJson id.name)]
  | .mvar id => Json.mkObj [("mvar", toJson id.name)]
  | .sort level => Json.mkObj [("sort", toJson (toString level))]
  | .const name levels => Json.mkObj [
      ("const", toJson name),
      ("levels", toJson (levels.map toString))]
  | .app function argument => Json.mkObj [
      ("app", Json.arr #[exprJson function, exprJson argument])]
  | .lam _name type body info => Json.mkObj [("lam", Json.mkObj [
      ("name", toJson "_"), ("type", exprJson type),
      ("body", exprJson body), ("binderInfo", toJson (binderInfoName info))])]
  | .forallE _name type body info => Json.mkObj [("forallE", Json.mkObj [
      ("name", toJson "_"), ("type", exprJson type),
      ("body", exprJson body), ("binderInfo", toJson (binderInfoName info))])]
  | .letE _name type value body nondep => Json.mkObj [("letE", Json.mkObj [
      ("name", toJson "_"), ("type", exprJson type),
      ("value", exprJson value), ("body", exprJson body),
      ("nondep", toJson nondep)])]
  | .lit (.natVal value) => Json.mkObj [("nat", toJson value)]
  | .lit (.strVal value) => Json.mkObj [("string", toJson value)]
  | .mdata _ body => exprJson body
  | .proj typeName index value => Json.mkObj [("proj", Json.mkObj [
      ("typeName", toJson typeName), ("index", toJson index),
      ("structure", exprJson value)])]


private def predicate (e : Expr) : MetaM Expr := do
  let args := e.getAppArgs
  if args.size < 4 || !e.getAppFn.isConst then
    throwError "bound predicate is not a named application"
  return mkAppN e.getAppFn (args.extract 0 (args.size - 4))

private def closeLaw (xs : Array Expr) (input output : Expr)
    (measureName : Name) (indices : Array Nat) : MetaM Expr := do
  let source ← predicate input
  if source != (← predicate output) then
    throwError "bound predicate applications differ"
  let mut args := #[]
  for i in indices do
    if i >= xs.size then throwError "measure argument is outside the observed telescope"
    args := args.push xs[i]!
  let measure ← mkAppOptM measureName (args.map some)
  let law ← mkAppM ``Ladon.RealBound.Admission #[source, measure]
  let law ← instantiateMVars law
  if law.hasExprMVar || law.hasLevelMVar then
    throwError "bound law has unresolved metavariables: {law}"
  let closed ← mkForallFVars xs law (usedOnly := true)
  -- Never turn unrelated hypotheses into evidence for the laws. Even retained
  -- proof-valued parameters are unsupported until a conditional profile exists.
  forallTelescope closed fun context _ => do
    for x in context do
      if ← isProp (← inferType x) then
        throwError "proof-valued bound parameters are unsupported"
  if closed.hasFVar then throwError "bound law has escaping local parameters"
  return closed

private partial def peel (e : Expr) (xs : Array Expr) (last : Option Expr)
    (measure : Name) (indices : Array Nat) (fuel : Nat) : MetaM Expr := do
  if fuel == 0 then throwError "bound telescope exceeds traversal limit"
  match e with
  | .forallE _name type body bi =>
    withLocalDecl (Name.mkSimple s!"bound{xs.size}") bi type fun x =>
      peel (body.instantiate1 x) (xs.push x) (some type) measure indices (fuel - 1)
  | _ =>
    let args := e.getAppArgs
    if e.getAppFn.isConstOf ``Exists && args.size == 2 then
      match args[1]! with
      | .lam _name type body bi =>
        withLocalDecl (Name.mkSimple s!"bound{xs.size}") bi type fun x =>
          peel (body.instantiate1 x) (xs.push x) last measure indices (fuel - 1)
      | _ => throwError "expected explicit bound witness lambda"
    else if e.getAppFn.isConstOf ``And && args.size == 2 then
      peel args[1]! xs last measure indices (fuel - 1)
    else
      match last with
      | some input => closeLaw xs input e measure indices
      | none => throwError "missing bound input premise"

/-- Derive a proposition from the live source declaration, not caller goal text. -/
elab "ladon_bound_admission% " target:str expected:str measure:str "[" indices:num,* "]" : term => do
  let targetName := target.getString.toName
  if ((← getEnv).getModuleIdxFor? targetName).isSome then
    throwError "bound declaration must belong to the copied source"
  let info ← getConstInfo targetName
  let normalized ← zetaReduce (← instantiateMVars info.type)
  let expected ← match Json.parse expected.getString with
    | .ok value => pure value
    | .error _ => throwError "invalid expected bound expression"
  if exprJson normalized != expected then
    throwError "live declaration differs from the observed bound expression"
  peel normalized #[] none measure.getString.toName
    (indices.getElems.map (·.getNat)) 128

end Ladon.RealBoundBinding
