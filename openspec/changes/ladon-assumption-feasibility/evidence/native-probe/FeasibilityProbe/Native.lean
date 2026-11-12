import Lean

namespace FeasibilityProbe.Native

open Lean Meta

inductive UnsupportedReason where
  | dependency
  | bounds
  | profile
  deriving Repr, Inhabited, BEq

inductive BuildResult where
  | supported (closedGoal : Expr)
  | unsupported (reason : UnsupportedReason)
  deriving Repr

private def supportedDataType (type : Expr) : MetaM Bool := do
  let type ← whnf type
  let matchesType (name : Name) : MetaM Bool := do
    let expected := mkConst name
    isDefEq type expected
  return (← matchesType ``Nat) || (← matchesType ``Int) || (← matchesType ``Rat)

private def isProofBinder (x : Expr) : MetaM Bool := do
  isProp (← inferType x)

private def mkAnd (p q : Expr) : Expr := mkApp2 (mkConst ``And) p q

private def closeExists (x : Expr) (body : Expr) : MetaM Expr := do
  let type ← inferType x
  let sort ← inferType type
  let level := sort.sortLevel!
  let predicate ← mkLambdaFVars #[x] body
  pure <| mkApp2 (mkConst ``Exists [level]) type predicate

/--
Builds the feasibility goal for the assumptions in a declaration telescope.
Data binders become existential variables and proof binders contribute their
propositions as conjunctions. The declaration's result type is deliberately
not included.
-/
def buildPremiseGoal (declarationType : Expr) : MetaM BuildResult := do
  if declarationType.hasMVar then
    return .unsupported .profile
  forallBoundedTelescope declarationType (some 65) fun xs body => do
    if xs.size > 64 then
      return .unsupported .bounds
    -- A let can conceal further binders and proof-derived local values.
    -- This declaration-only experiment does not yet close that telescope.
    match body with
    | .letE .. | .mdata .. => return .unsupported .profile
    | _ => pure ()
    if !(← isProp body) then
      return .unsupported .profile
    let mut proofBinders : Array Expr := #[]
    let mut dataBinders : Array Expr := #[]
    let mut hypothesisCount := 0
    for x in xs do
      let type ← inferType x
      if ← isProofBinder x then
        hypothesisCount := hypothesisCount + 1
        if hypothesisCount > 128 then
          return .unsupported .bounds
        proofBinders := proofBinders.push x
      else
        dataBinders := dataBinders.push x
        -- Proof terms are not existential data. If a later data domain refers
        -- to one, the feasibility projection cannot faithfully close it.
        for proofBinder in proofBinders do
          if type.containsFVar proofBinder.fvarId! then
            return .unsupported .dependency
        if !(← supportedDataType type) then
          return .unsupported .profile
    -- A later proof proposition depending on an earlier proof witness cannot
    -- be represented by a conjunction of propositions alone.
    for proofBinder in proofBinders do
      let type ← inferType proofBinder
      for earlierProof in proofBinders do
        if earlierProof == proofBinder then
          break
        if type.containsFVar earlierProof.fvarId! then
          return .unsupported .dependency
    let mut props : Array Expr := #[]
    for proofBinder in proofBinders do
      props := props.push (← inferType proofBinder)
    let mut goal := mkConst ``True
    if props.size == 1 then
      goal := props[0]!
    else if props.size > 1 then
      goal := props[props.size - 1]!
      for i in [:props.size - 1] do
        goal := mkAnd props[props.size - 2 - i]! goal
    for x in dataBinders.reverse do
      goal ← closeExists x goal
    if goal.hasAnyFVar (fun _ => true) || goal.hasMVar || goal.hasLooseBVars then
      return .unsupported .dependency
    return .supported goal

end FeasibilityProbe.Native
