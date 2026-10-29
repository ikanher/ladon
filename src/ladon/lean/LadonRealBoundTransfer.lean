import LadonRealBoundScalars
import LadonRealBoundComposition

namespace Ladon.RealBoundTransfer
open Lean Meta Elab Term

universe u v w p

/-- The two transfers remain explicit assumptions, with their actual source products. -/
theorem composeActual {X : Type u} {Y : Type v} {Z : Type w} {P : Type p}
    (J : X → Set P → Nat → Real → Prop) (Q : Y → Set P → Nat → Real → Prop)
    (R : Z → Set P → Nat → Real → Prop) (x : X) (y : Y) (z : Z)
    (S : Set P) (m n r : Nat) (C K L actual₁ actual₂ : Real)
    (eq₁ : actual₁ = K*C) (eq₂ : actual₂ = L*actual₁)
    (first : 0 ≤ K ∧ (0 ≤ C → J x S m C → Q y S n actual₁))
    (second : 0 ≤ L ∧ (0 ≤ actual₁ → Q y S n actual₁ → R z S r actual₂)) :
    Ladon.RealBound.TransferAt J R x z S m r C (L*K) := by
  subst actual₁
  subst actual₂
  exact Ladon.RealBound.transfer_compose first second

private def arrow (name : String) (a b : Expr) : Expr :=
  .forallE (Name.mkSimple name) a b .default

private def predicate (e : Expr) : MetaM Expr := do
  let a := e.getAppArgs
  if a.size < 4 || !e.getAppFn.isConst then throwError "transfer predicate is not a named application"
  return mkAppN e.getAppFn (a.extract 0 (a.size - 4))

private def specialize (term expected : Expr) : MetaM Expr := do
  let (args, _, body) ← forallMetaTelescope (← inferType term)
  unless ← isDefEq body expected do throwError "transfer scalar evidence differs from source"
  let applied ← instantiateMVars (mkAppN term args)
  if applied.hasExprMVar || applied.hasLevelMVar then throwError "unresolved transfer scalar evidence"
  return applied

private def validate (xs : Array Expr) (input output K guardK : Expr)
    (roles : Array Nat) (loss : Nat) : MetaM Expr := do
  if roles.size != 6 || roles.toList.eraseDups.length != 6 then throwError "invalid transfer role indices"
  for i in roles do
    if i >= xs.size then throwError "transfer role outside telescope"
  let _ ← predicate input
  let _ ← predicate output
  let a := input.getAppArgs
  let b := output.getAppArgs
  for (offset, index) in [(4, roles[1]!), (3, roles[2]!), (1, roles[3]!)] do
    unless ← isDefEq a[a.size - offset]! xs[index]! do throwError "transfer input role differs"
  unless xs[roles[4]!]! == K do throwError "transfer coefficient is not the source witness"
  unless ← isDefEq (← inferType xs[roles[0]!]!) (mkConst ``Nat) do throwError "transfer order is not Nat"
  let order ← mkAppM ``Nat.add #[xs[roles[0]!]!, toExpr loss]
  unless ← isDefEq a[a.size - 2]! order do throwError "transfer loss differs from observed order"
  unless ← isDefEq b[b.size - 2]! xs[roles[0]!]! do throwError "transfer output order differs"
  unless ← isDefEq a[a.size - 3]! b[b.size - 3]! do throwError "transfer set differs"
  unless ← isDefEq (← predicate input) (← predicate output) do throwError "transfer predicate differs"
  let law ← Ladon.RealScalarBinding.scalarLawBody xs input output K guardK roles[5]!
  let _ ← Ladon.RealScalarBinding.closeData xs (← mkAppM ``And #[input, ← mkAppM ``And #[output, law]])
  return law

private def checkData (xs replacements : Array Expr) : MetaM Unit := do
  for index in [:xs.size] do
    let type ← inferType xs[index]!
    if !(← isProp type) then
      let expected := type.replaceFVars xs replacements
      unless ← isDefEq (← inferType replacements[index]!) expected do
        throwError "transfer substitution changes a dependent data type"

private def rightMap (xs ys : Array Expr) (roles : Array Nat) (firstOutput L : Expr) : MetaM (Array Expr) := do
  if xs.size != ys.size then throwError "transfer telescope layouts differ"
  let a := firstOutput.getAppArgs
  let mut replacements := xs
  replacements := replacements.set! roles[1]! a[a.size - 4]!
  replacements := replacements.set! roles[2]! a[a.size - 3]!
  replacements := replacements.set! roles[3]! a.back!
  replacements := replacements.set! roles[4]! L
  for index in [:xs.size] do
    let x ← xs[index]!.fvarId!.getDecl
    let y ← ys[index]!.fvarId!.getDecl
    if x.binderInfo != y.binderInfo || (← isProp x.type) != (← isProp y.type) then
      throwError "transfer binder roles or information differ"
  checkData ys replacements
  return replacements

private def premise (input output C K : Expr) : MetaM Expr := do
  mkAppM ``And #[← mkAppM ``Ladon.RealScalars.nonnegative #[K],
    arrow "transferSign" (← mkAppM ``Ladon.RealScalars.nonnegative #[C])
      (arrow "transferInput" input output)]

private def close (xs : Array Expr) (a mid final K L lawA lawB : Expr)
    (evidence : Option (Expr × Expr)) : MetaM Expr := do
  let aa := a.getAppArgs
  let bb := mid.getAppArgs
  let cc := final.getAppArgs
  let J ← predicate a
  let Q ← predicate mid
  let R ← predicate final
  let C := aa.back!
  let first ← premise a mid C K
  let second ← premise mid final bb.back! L
  let product ← mkAppM ``Ladon.RealScalars.product #[L, K]
  let target ← mkAppM ``Ladon.RealBound.TransferAt #[J, R, aa[aa.size-4]!, cc[cc.size-4]!,
    aa[aa.size-3]!, aa[aa.size-2]!, cc[cc.size-2]!, C, product]
  let goal ← mkForallFVars xs (arrow "firstTransfer" first (arrow "secondTransfer" second target)) (usedOnly := true)
  if goal.hasFVar then throwError "escaping transfer locals"
  match evidence with
  | none => return goal
  | some (sa, sb) =>
    let sa ← specialize sa lawA
    let sb ← specialize sb lawB
    let eqA ← mkAppM ``And.right #[← mkAppM ``And.right #[sa]]
    let eqB ← mkAppM ``And.right #[← mkAppM ``And.right #[sb]]
    let proof ← mkAppM ``composeActual #[J, Q, R, aa[aa.size-4]!, bb[bb.size-4]!, cc[cc.size-4]!,
      aa[aa.size-3]!, aa[aa.size-2]!, bb[bb.size-2]!, cc[cc.size-2]!, C, K, L, bb.back!, cc.back!, eqA, eqB]
    let proof ← mkLambdaFVars xs (← instantiateMVars proof) (usedOnly := true)
    unless ← isDefEq (← inferType proof) goal do throwError "transfer proof has unexpected dependencies"
    return proof

private def build (xs : Array Expr) (a b K guardK : Expr)
    (ys : Array Expr) (c d H guardH : Expr) (roles : Array Nat) (lossA lossB : Nat)
    (evidence : Option (Expr × Expr)) : MetaM Expr := do
  let lawA ← validate xs a b K guardK roles lossA
  let lawB ← validate ys c d H guardH roles lossB
  let shifted ← mkAppM ``Nat.add #[xs[roles[0]!]!, toExpr lossB]
  let firstMap := xs.set! roles[0]! shifted
  checkData xs firstMap
  let a := a.replaceFVars xs firstMap
  let b := b.replaceFVars xs firstMap
  let lawA := lawA.replaceFVars xs firstMap
  withLocalDeclD (Name.mkSimple "secondCoefficient") (mkConst ``Real) fun L => do
    let mapping ← rightMap xs ys roles b L
    let c := c.replaceFVars ys mapping
    let d := d.replaceFVars ys mapping
    unless ← isDefEq b c do throwError "transfer intermediate predicate, object, set, order or bound differs"
    let lawB := lawB.replaceFVars ys mapping
    let all := xs.push L
    let _ ← Ladon.RealScalarBinding.closeData all (← mkAppM ``And #[a, ← mkAppM ``And #[b, d]])
    close all a b d K L lawA lawB evidence

private def parseExpected (s : TSyntax `str) : TermElabM Json :=
  match Json.parse s.getString with
  | .ok value => pure value
  | .error _ => throwError "invalid observed transfer expression"

private def derive (left right : Name) (a b : Json) (roles : Array Nat) (lossA lossB : Nat)
    (evidence : Option (Expr × Expr)) : MetaM Expr :=
  Ladon.RealScalarBinding.withObservedScalarContext left a fun xs input output K guardK =>
    Ladon.RealScalarBinding.withObservedScalarContext right b fun ys inputB outputB L guardL =>
      build xs input output K guardK ys inputB outputB L guardL roles lossA lossB evidence

elab "ladon_real_bound_compose% " left:str expectedA:str right:str expectedB:str
    "[" roles:num,* "]" lossA:num lossB:num : term => do
  derive left.getString.toName right.getString.toName (← parseExpected expectedA) (← parseExpected expectedB)
    (roles.getElems.map (·.getNat)) lossA.getNat lossB.getNat none

elab "ladon_real_bound_compose_proof% " left:str expectedA:str right:str expectedB:str
    "[" roles:num,* "]" lossA:num lossB:num scalarA:term:max scalarB:term:max : term => do
  let sa ← elabTerm scalarA none
  let sb ← elabTerm scalarB none
  derive left.getString.toName right.getString.toName (← parseExpected expectedA) (← parseExpected expectedB)
    (roles.getElems.map (·.getNat)) lossA.getNat lossB.getNat (some (sa, sb))

end Ladon.RealBoundTransfer
