import LadonRealBoundScalars

namespace Ladon.RealBoundCoefficient
open Lean Meta Elab Term

/-- Only the last scalar bound changes. All endpoint parameters remain fixed. -/
theorem weaken {X P Y : Type} {J : X → Set P → Nat → Real → Prop}
    {measure : X → P → Y → Nat → Real} (admitted : Ladon.RealBound.Admission J measure)
    (x : X) (S : Set P) (n : Nat) (K C L actual : Real)
    (product : actual = K * C) (hKL : K ≤ L) (hC : 0 ≤ C) :
    J x S n actual → J x S n (L * C) := by
  apply admitted.2.2
  rw [product]
  exact mul_le_mul_of_nonneg_right hKL hC

private def parseExpected (value : TSyntax `str) : TermElabM Json :=
  match Json.parse value.getString with
  | .ok parsed => pure parsed
  | .error _ => throwError "invalid expected coefficient expression JSON"

private def specialize (e expected : Expr) : MetaM Expr := do
  let (args, _, body) ← forallMetaTelescope (← inferType e)
  unless ← isDefEq body expected do
    throwError "coefficient evidence does not match its source-bound law"
  let applied ← instantiateMVars (mkAppN e args)
  if applied.hasExprMVar || applied.hasLevelMVar then
    throwError "coefficient evidence has unresolved parameters"
  return applied

private def admissionAt (admitted predicate : Expr) : MetaM Expr := do
  let (args, _, body) ← forallMetaTelescope (← inferType admitted)
  let a := body.getAppArgs
  if !body.getAppFn.isConstOf ``Ladon.RealBound.Admission || a.size < 2 then
    throwError "coefficient rule requires a checked Admission term"
  unless ← isDefEq a[a.size - 2]! predicate do
    throwError "coefficient admission belongs to a different predicate"
  let applied ← instantiateMVars (mkAppN admitted args)
  if applied.hasExprMVar || applied.hasLevelMVar then
    throwError "coefficient admission has unresolved parameters"
  return applied

private def build (xs : Array Expr) (input output K guardK : Expr)
    (guardIndex : Nat) (evidence : Option (Expr × Expr)) : MetaM Expr := do
  if xs.isEmpty then throwError "missing coefficient source context"
  unless ← isDefEq (← inferType xs.back!) input do
    throwError "coefficient source does not end in its input premise"
  let a := output.getAppArgs
  let b := input.getAppArgs
  if a.size < 4 || b.size < 4 then throwError "missing coefficient applications"
  let predicate := mkAppN output.getAppFn (a.extract 0 (a.size - 4))
  let C := b.back!
  let scalarLaw ← Ladon.RealScalarBinding.scalarLawBody xs input output K guardK guardIndex
  -- This checks retained dependencies even if evidence specializes away a binder.
  let _ ← Ladon.RealScalarBinding.closeData xs.pop (← mkAppM ``And #[output, scalarLaw])
  withLocalDeclD (Name.mkSimple "coefficientLimit") (mkConst ``Real) fun L => do
    let hKLType ← mkAppM ``LE.le #[K, L]
    let hCType ← mkAppM ``Ladon.RealScalars.nonnegative #[C]
    let targetBound ← mkAppM ``Ladon.RealScalars.product #[L, C]
    let target := mkAppN output.getAppFn ((a.pop).push targetBound)
    withLocalDeclD (Name.mkSimple "coefficientOrder") hKLType fun hKL => do
      withLocalDeclD (Name.mkSimple "coefficientSign") hCType fun hC => do
        withLocalDeclD (Name.mkSimple "coefficientOutput") output fun hOut => do
          let binders := #[L, hKL, hC, hOut]
          let openGoal ← mkForallFVars binders target
          let goal ← mkForallFVars xs.pop openGoal (usedOnly := true)
          if goal.hasFVar then throwError "escaping coefficient locals"
          match evidence with
          | none => return goal
          | some (admitted, scalars) =>
            let admitted ← admissionAt admitted predicate
            let scalars ← specialize scalars scalarLaw
            let product ← mkAppM ``And.right #[← mkAppM ``And.right #[scalars]]
            let result ← mkAppM ``weaken #[admitted, a[a.size - 4]!, a[a.size - 3]!,
              a[a.size - 2]!, K, C, L, a.back!, product, hKL, hC, hOut]
            let result ← mkLambdaFVars binders (← instantiateMVars result)
            let closed ← mkLambdaFVars xs.pop result (usedOnly := true)
            unless ← isDefEq (← inferType closed) goal do
              throwError "coefficient proof has unexpected data dependencies"
            return closed

elab "ladon_real_bound_coefficient% " target:str expected:str guardIndex:num : term => do
  Ladon.RealScalarBinding.withObservedScalarContext target.getString.toName
    (← parseExpected expected) fun xs input output K guardK =>
      build xs input output K guardK guardIndex.getNat none

elab "ladon_real_bound_coefficient_proof% " target:str expected:str guardIndex:num
    admitted:term:max scalars:term:max : term => do
  let admitted ← elabTerm admitted none
  let scalars ← elabTerm scalars none
  Ladon.RealScalarBinding.withObservedScalarContext target.getString.toName
    (← parseExpected expected) fun xs input output K guardK =>
      build xs input output K guardK guardIndex.getNat (some (admitted, scalars))

end Ladon.RealBoundCoefficient
