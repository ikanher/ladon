import Lean
import Mathlib.Analysis.Calculus.ContDiff.Basic
open Lean Meta Elab Command
namespace ScopedAliasProbe
noncomputable def product [HMul Real Real Real] (K C : Real) : Real := K * C
end ScopedAliasProbe

private def forallCount : Expr → Nat
  | .forallE _ _ body _ => 1 + forallCount body
  | _ => 0

elab "#scoped_alias_kernel_probe" : command => do
  liftTermElabM do
    let real := mkConst ``Real
    let instanceType := mkAppN (mkConst ``HMul [.zero, .zero, .zero]) #[real, real, real]
    withLocalDeclD `n (mkConst ``Nat) fun n => do
    withLocalDecl `selected .instImplicit instanceType fun selected => do
    withLocalDeclD `K real fun k => do
    withLocalDeclD `C real fun c => do
    withLocalDeclD `guard (mkConst ``True) fun guard => do
      let scope := #[n, selected, k, c, guard]
      let original := mkAppN (mkConst ``ScopedAliasProbe.product) #[selected, k, c]
      let canonical := mkAppN (mkConst ``HMul.hMul [.zero, .zero, .zero])
        #[real, real, real, selected, k, c]
      let type ← mkForallFVars scope (← mkEq original canonical) (usedOnly := false)
      let proof ← mkLambdaFVars scope (← mkEqRefl original) (usedOnly := false)
      unless forallCount type == 5 do throwError "unused source binders were dropped"
      if type.hasFVar || type.hasMVar || proof.hasFVar || proof.hasMVar then
        throwError "certificate is not closed"
      let decl := Declaration.thmDecl {
        name := `ScopedAliasProbe.checked
        levelParams := []
        type := type
        value := proof }
      let options := debug.skipKernelTC.set ({} : Options) false
      match (← getEnv).toKernelEnv.addDecl options decl with
      | .error _ => throwError "exact-instance certificate rejected"
      | .ok _ => pure ()
      addDecl decl
      logInfo "exact instance and all five source binders preserved"
      let defaultInstance ← synthInstance instanceType
      -- To force a different instance, build the global instance outside local synthesis.
      let globalProduct := mkAppN (mkConst ``HMul.hMul [.zero, .zero, .zero])
        #[real, real, real, mkAppN (mkConst ``instHMul [.zero]) #[real, mkConst ``Real.instMul], k, c]
      let _ := defaultInstance
      let wrongType ← mkForallFVars scope (← mkEq original globalProduct) (usedOnly := false)
      let wrongDecl := Declaration.thmDecl {
        name := `ScopedAliasProbe.wrongInstance
        levelParams := []
        type := wrongType
        value := proof }
      match (← getEnv).toKernelEnv.addDecl options wrongDecl with
      | .error _ => logInfo "different instance rejected synchronously"
      | .ok _ => throwError "different instance accepted"
      let missing ← mkLambdaFVars #[n, k, c, guard] (← mkEqRefl original) (usedOnly := false)
      unless missing.hasFVar do throwError "missing instance was not exposed as a free variable"
      logInfo "omitted source instance detected before checking"
#scoped_alias_kernel_probe
#print axioms ScopedAliasProbe.checked
