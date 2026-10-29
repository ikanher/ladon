import Lean
import Lean.Meta.Transform
import LadonRealBound

namespace Ladon.RealScalars

def nonnegative (x : Real) : Prop := 0 ≤ x
def product (K C : Real) : Real := K * C

end Ladon.RealScalars

namespace Ladon.RealScalarBinding
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


private def closeData (xs : Array Expr) (law : Expr) : MetaM Expr := do
  let law ← instantiateMVars law
  if law.hasExprMVar || law.hasLevelMVar then throwError "unresolved scalar metavariables"
  let closed ← mkForallFVars xs law (usedOnly := true)
  forallTelescope closed fun context _ => do
    for x in context do
      if ← isProp (← inferType x) then
        throwError "scalar semantics cannot inherit proof assumptions"
  if closed.hasFVar then throwError "escaping scalar locals"
  return closed

private def scalarLaw (xs : Array Expr) (input output K guardK : Expr)
    (guardIndex : Nat) : MetaM Expr := do
  let inputArgs := input.getAppArgs
  let outputArgs := output.getAppArgs
  if inputArgs.size < 4 || outputArgs.size < 4 || guardIndex >= xs.size then
    throwError "missing scalar source applications"
  let C := inputArgs.back!
  let guardC ← inferType xs[guardIndex]!
  let canonicalK ← mkAppM ``Ladon.RealScalars.nonnegative #[K]
  let canonicalC ← mkAppM ``Ladon.RealScalars.nonnegative #[C]
  let canonicalProduct ← mkAppM ``Ladon.RealScalars.product #[K, C]
  let a ← mkEq guardK canonicalK
  let b ← mkEq guardC canonicalC
  let c ← mkEq outputArgs.back! canonicalProduct
  closeData xs (← mkAppM ``And #[a, ← mkAppM ``And #[b, c]])

private partial def walk (e : Expr) (xs : Array Expr) (last witness guard : Option Expr)
    (guardIndex fuel : Nat) : MetaM Expr := do
  if fuel == 0 then throwError "scalar telescope exceeds limit"
  match e with
  | .forallE _ type body bi =>
    withLocalDecl (Name.mkSimple s!"scalar{xs.size}") bi type fun x =>
      walk (body.instantiate1 x) (xs.push x) (some type) witness guard guardIndex (fuel - 1)
  | _ =>
    let args := e.getAppArgs
    if e.getAppFn.isConstOf ``Exists && args.size == 2 then
      if witness.isSome then throwError "multiple scalar witnesses"
      match args[1]! with
      | .lam _ type body bi =>
        withLocalDecl (Name.mkSimple s!"scalar{xs.size}") bi type fun x =>
          walk (body.instantiate1 x) (xs.push x) last (some x) guard guardIndex (fuel - 1)
      | _ => throwError "missing scalar witness lambda"
    else if e.getAppFn.isConstOf ``And && args.size == 2 then
      if guard.isSome then throwError "multiple scalar conjunction guards"
      walk args[1]! xs last witness (some args[0]!) guardIndex (fuel - 1)
    else
      match last, witness, guard with
      | some input, some K, some guardK => scalarLaw xs input e K guardK guardIndex
      | _, _, _ => throwError "incomplete scalar source context"

elab "ladon_scalar_admission% " target:str expected:str guardIndex:num : term => do
  let name := target.getString.toName
  if ((← getEnv).getModuleIdxFor? name).isSome then
    throwError "scalar target must belong to copied source"
  let info ← getConstInfo name
  let actual ← zetaReduce (← instantiateMVars info.type)
  let expected ← match Json.parse expected.getString with
    | .ok value => pure value
    | .error _ => throwError "invalid expected scalar expression"
  if exprJson actual != expected then
    throwError "live scalar declaration differs from observation"
  walk actual #[] none none none guardIndex.getNat 128

end Ladon.RealScalarBinding
