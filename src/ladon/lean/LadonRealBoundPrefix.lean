import LadonRealBoundBinding

namespace Ladon.RealBoundPrefix
open Lean Meta Elab Term

private def parseExpected (value : TSyntax `str) : TermElabM Json :=
  match Json.parse value.getString with
  | .ok parsed => pure parsed
  | .error _ => throwError "invalid expected prefix expression JSON"

private def validateInputs (xs : Array Expr) (strong weak : Expr)
    (orderIndex high low : Nat) : MetaM (Expr × Expr × Expr) := do
  let a := strong.getAppArgs
  let b := weak.getAppArgs
  if a.size < 4 || b.size < 4 || orderIndex >= xs.size then
    throwError "prefix input application is incomplete"
  let predA := mkAppN strong.getAppFn (a.extract 0 (a.size - 4))
  let predB := mkAppN weak.getAppFn (b.extract 0 (b.size - 4))
  unless ← isDefEq predA predB do throwError "prefix predicates differ"
  for offset in [4, 3, 1] do
    unless ← isDefEq a[a.size - offset]! b[b.size - offset]! do
      throwError "prefix objects, sets or bounds differ"
  let n := xs[orderIndex]!
  unless ← isDefEq (← inferType n) (mkConst ``Nat) do
    throwError "prefix base order is not Nat"
  let expectedHigh ← mkAppM ``Nat.add #[n, toExpr high]
  let expectedLow ← mkAppM ``Nat.add #[n, toExpr low]
  unless ← isDefEq a[a.size - 2]! expectedHigh do
    throwError "strong prefix order differs from observed literal loss"
  unless ← isDefEq b[b.size - 2]! expectedLow do
    throwError "weak prefix order differs from observed literal loss"
  -- mkArrow generates a hygienic binder name tied to the temporary module.
  -- Capture and independent replay require the same structural goal identity.
  return (predA, n, .forallE (Name.mkSimple "prefixInput") strong weak .default)

private def applyAdmission (admission predicate : Expr) : MetaM Expr := do
  let (args, _, body) ← forallMetaTelescope (← inferType admission)
  let bodyArgs := body.getAppArgs
  if !body.getAppFn.isConstOf ``Ladon.RealBound.Admission || bodyArgs.size < 2 then
    throwError "prefix rule requires a checked Admission term"
  unless ← isDefEq bodyArgs[bodyArgs.size - 2]! predicate do
    throwError "prefix admission belongs to a different predicate"
  let applied ← instantiateMVars (mkAppN admission args)
  if applied.hasExprMVar || applied.hasLevelMVar then
    throwError "prefix admission has unresolved parameters"
  mkAppM ``And.left #[← mkAppM ``And.right #[applied]]

private def proof (xs : Array Expr) (strong weak admission : Expr)
    (orderIndex high low : Nat) : MetaM Expr := do
  let (predicate, n, _) ← validateInputs xs strong weak orderIndex high low
  let admittedPrefix ← applyAdmission admission predicate
  let numericGoal ← mkAppM ``LE.le #[toExpr low, toExpr high]
  let numericProof ← mkDecideProof numericGoal
  let orderProof ← mkAppM ``Nat.add_le_add_left #[numericProof, n]
  let a := strong.getAppArgs
  let b := weak.getAppArgs
  let result := mkAppN admittedPrefix #[a[a.size - 4]!, a[a.size - 3]!,
    b[b.size - 2]!, a[a.size - 2]!, a.back!, orderProof]
  let result ← instantiateMVars result
  let closed ← mkLambdaFVars xs result (usedOnly := true)
  return closed

elab "ladon_real_bound_prefix% " strong:str strongExpected:str weak:str weakExpected:str
    orderIndex:num high:num low:num : term => do
  Ladon.RealBoundBinding.withObservedBoundInputs
    strong.getString.toName (← parseExpected strongExpected)
    weak.getString.toName (← parseExpected weakExpected) fun xs a b => do
      let (_, _, goal) ← validateInputs xs a b orderIndex.getNat high.getNat low.getNat
      mkForallFVars xs goal (usedOnly := true)

elab "ladon_real_bound_prefix_proof% " strong:str strongExpected:str weak:str weakExpected:str
    orderIndex:num high:num low:num admission:term : term => do
  let admission ← elabTerm admission none
  Ladon.RealBoundBinding.withObservedBoundInputs
    strong.getString.toName (← parseExpected strongExpected)
    weak.getString.toName (← parseExpected weakExpected) fun xs a b =>
      proof xs a b admission orderIndex.getNat high.getNat low.getNat

end Ladon.RealBoundPrefix
