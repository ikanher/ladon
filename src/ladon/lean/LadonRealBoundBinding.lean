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

abbrev BoundMeasureBuilder := Array Expr → Expr → MetaM Expr

private def closeLaw (xs : Array Expr) (input output : Expr)
    (builder : BoundMeasureBuilder) : MetaM Expr := do
  let source ← predicate input
  if source != (← predicate output) then
    throwError "bound predicate applications differ"
  let measure ← builder xs source
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
    (builder : BoundMeasureBuilder) (fuel : Nat) : MetaM Expr := do
  if fuel == 0 then throwError "bound telescope exceeds traversal limit"
  match e with
  | .forallE _name type body bi =>
    withLocalDecl (Name.mkSimple s!"bound{xs.size}") bi type fun x =>
      peel (body.instantiate1 x) (xs.push x) (some type) builder (fuel - 1)
  | _ =>
    let args := e.getAppArgs
    if e.getAppFn.isConstOf ``Exists && args.size == 2 then
      match args[1]! with
      | .lam _name type body bi =>
        withLocalDecl (Name.mkSimple s!"bound{xs.size}") bi type fun x =>
          peel (body.instantiate1 x) (xs.push x) last builder (fuel - 1)
      | _ => throwError "expected explicit bound witness lambda"
    else if e.getAppFn.isConstOf ``And && args.size == 2 then
      peel args[1]! xs last builder (fuel - 1)
    else
      match last with
      | some input => closeLaw xs input e builder
      | none => throwError "missing bound input premise"

private partial def withInputPremise {α : Type} (e : Expr) (xs : Array Expr)
    (last : Option Expr) (fuel : Nat) (k : Array Expr → Expr → MetaM α) : MetaM α := do
  if fuel == 0 then throwError "bound comparison telescope exceeds traversal limit"
  match e with
  | .forallE _name type body bi =>
    withLocalDecl (Name.mkSimple s!"compare{xs.size}") bi type fun x =>
      withInputPremise (body.instantiate1 x) (xs.push x) (some type) (fuel - 1) k
  | _ =>
    let args := e.getAppArgs
    if e.getAppFn.isConstOf ``Exists && args.size == 2 then
      match args[1]! with
      | .lam _name type body bi =>
        withLocalDecl (Name.mkSimple s!"compare{xs.size}") bi type fun x =>
          withInputPremise (body.instantiate1 x) (xs.push x) last (fuel - 1) k
      | _ => throwError "expected explicit bound witness lambda"
    else if e.getAppFn.isConstOf ``And && args.size == 2 then
      withInputPremise args[1]! xs last (fuel - 1) k
    else
      match last with
      | some input => k xs input
      | none => throwError "missing bound input premise"

private def observedType (targetName : Name) (expected : Json) : MetaM Expr := do
  if ((← getEnv).getModuleIdxFor? targetName).isSome then
    throwError "bound declaration must belong to the copied source"
  let info ← getConstInfo targetName
  let normalized ← zetaReduce (← instantiateMVars info.type)
  if exprJson normalized != expected then
    throwError "live declaration differs from the observed bound expression"
  pure normalized

/-- Expose the same canonical typed view for source-owned relation planning. -/
def observedTypeJson (targetName : Name) : MetaM Json := do
  if ((← getEnv).getModuleIdxFor? targetName).isSome then
    throwError "bound declaration must belong to the copied source"
  let info ← getConstInfo targetName
  let normalized ← zetaReduce (← instantiateMVars info.type)
  pure (exprJson normalized)

/-- Build an exact input-predicate relation from both currently elaborated declarations. -/
def observedBoundRelation (leftName : Name) (leftExpected : Json)
    (rightName : Name) (rightExpected : Json) : MetaM Expr := do
  let leftType ← observedType leftName leftExpected
  let rightType ← observedType rightName rightExpected
  withInputPremise leftType #[] none 128 fun leftLocals leftInput => do
    withInputPremise rightType #[] none 128 fun rightLocals rightInput => do
      if leftLocals.size != rightLocals.size then
        throwError "bound relation contexts have different telescope lengths"
      for index in [:leftLocals.size] do
        let leftType ← inferType leftLocals[index]!
        let rightType ← inferType rightLocals[index]!
        let alignedRightType := rightType.replaceFVars (rightLocals.take index) (leftLocals.take index)
        unless ← isDefEq leftType alignedRightType do
          throwError "bound relation contexts have incompatible binder types"
      let alignedRight := rightInput.replaceFVars rightLocals leftLocals
      unless ← isDefEq (← inferType leftInput) (← inferType alignedRight) do
        throwError "bound relation premises have incompatible proposition types"
      let relation ← mkAppM ``Iff #[leftInput, alignedRight]
      let closed ← mkForallFVars leftLocals relation (usedOnly := true)
      if closed.hasFVar then throwError "bound relation has escaping local parameters"
      pure closed

/-- Align source data while excluding the input proof being related.
    The original equivalence builder is deliberately unchanged. -/
def withObservedBoundInputs {α : Type} (strongName : Name) (strongExpected : Json)
    (weakName : Name) (weakExpected : Json)
    (k : Array Expr → Expr → Expr → MetaM α) : MetaM α := do
  let strongType ← observedType strongName strongExpected
  let weakType ← observedType weakName weakExpected
  withInputPremise strongType #[] none 128 fun strongLocals strongInput => do
    withInputPremise weakType #[] none 128 fun weakLocals weakInput => do
      if strongLocals.isEmpty || strongLocals.size != weakLocals.size then
        throwError "prefix contexts have different telescope lengths"
      unless ← isDefEq (← inferType strongLocals.back!) strongInput do
        throwError "prefix source does not end in its input premise"
      unless ← isDefEq (← inferType weakLocals.back!) weakInput do
        throwError "prefix target does not end in its input premise"
      let strongData := strongLocals.pop
      let weakData := weakLocals.pop
      for index in [:strongData.size] do
        let a ← strongData[index]!.fvarId!.getDecl
        let b ← weakData[index]!.fvarId!.getDecl
        if a.binderInfo != b.binderInfo then throwError "prefix binder information differs"
        let aligned := b.type.replaceFVars (weakData.take index) (strongData.take index)
        unless ← isDefEq a.type aligned do
          throwError "prefix data binder types differ"
      let alignedWeak := weakInput.replaceFVars weakData strongData
      -- Use a conjunction to inspect only data dependencies, without mistaking
      -- the implication's own antecedent for an inherited proof assumption.
      let joint ← mkAppM ``And #[strongInput, alignedWeak]
      let dataGoal ← mkForallFVars strongData joint (usedOnly := true)
      forallTelescope dataGoal fun xs _ => do
        for x in xs do
          if ← isProp (← inferType x) then
            throwError "conditional prefix dependencies are unsupported"
      k strongData strongInput alignedWeak

/-- Derive the checked relation goal from both live source declarations. -/
elab "ladon_real_bound_relation% " leftTarget:str leftExpected:str
    rightTarget:str rightExpected:str : term => do
  let parseExpected (value : TSyntax `str) : TermElabM Json :=
    match Json.parse value.getString with
    | .ok parsed => pure parsed
    | .error _ => throwError "invalid expected bound expression JSON"
  let leftJson ← parseExpected leftExpected
  let rightJson ← parseExpected rightExpected
  observedBoundRelation leftTarget.getString.toName leftJson
    rightTarget.getString.toName rightJson

/-- Share exact live statement binding and scope checks across closed adapters. -/
def observedBoundLaw (targetName : Name) (expected : Json)
    (builder : BoundMeasureBuilder) : MetaM Expr := do
  if ((← getEnv).getModuleIdxFor? targetName).isSome then
    throwError "bound declaration must belong to the copied source"
  let info ← getConstInfo targetName
  let normalized ← zetaReduce (← instantiateMVars info.type)
  if exprJson normalized != expected then
    throwError "live declaration differs from the observed bound expression"
  peel normalized #[] none builder 128

private def namedMeasure (measureName : Name) (indices : Array Nat) : BoundMeasureBuilder :=
  fun xs _ => do
    let mut args := #[]
    for i in indices do
      if i >= xs.size then throwError "measure argument is outside the observed telescope"
      args := args.push xs[i]!
    mkAppOptM measureName (args.map some)

/-- Derive a proposition from the live source declaration, not caller goal text. -/
elab "ladon_bound_admission% " target:str expected:str measure:str "[" indices:num,* "]" : term => do
  let expected ← match Json.parse expected.getString with
    | .ok value => pure value
    | .error _ => throwError "invalid expected bound expression"
  observedBoundLaw target.getString.toName expected
    (namedMeasure measure.getString.toName (indices.getElems.map (·.getNat)))

end Ladon.RealBoundBinding
