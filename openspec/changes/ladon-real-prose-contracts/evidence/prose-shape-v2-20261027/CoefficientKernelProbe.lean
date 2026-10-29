import Lean
import Mathlib.Analysis.Calculus.ContDiff.Basic
open Lean Meta Elab Command
namespace AliasKernelProbe
noncomputable def bump (n : Real) : Real := n * n
noncomputable def bad (n : Real) : Real := n * (n + 1)
end AliasKernelProbe

elab "#alias_kernel_probe" : command => do
  liftTermElabM do
    withLocalDeclD `n (mkConst ``Real) fun n => do
      let original := mkApp (mkConst ``AliasKernelProbe.bump) n
      let canonical ← mkAppM ``HMul.hMul #[n, n]
      let eq ← mkEq original canonical
      let goal ← mkForallFVars #[n] eq
      let proof ← mkLambdaFVars #[n] (← mkEqRefl original)
      let decl := Declaration.thmDecl {
        name := `AliasKernelProbe.checked
        levelParams := []
        type := goal
        value := proof }
      let options := debug.skipKernelTC.set ({} : Options) false
      match (← getEnv).toKernelEnv.addDecl options decl with
      | .error _ => throwError "correct alias certificate rejected synchronously"
      | .ok _ => pure ()
      addDecl decl
      logInfo "correct alias kernel certificate accepted synchronously"
      let badOriginal := mkApp (mkConst ``AliasKernelProbe.bad) n
      let badGoal ← mkForallFVars #[n] (← mkEq badOriginal canonical)
      let badProof ← mkLambdaFVars #[n] (← mkEqRefl badOriginal)
      let badDecl := Declaration.thmDecl {
        name := `AliasKernelProbe.mustNotExist
        levelParams := []
        type := badGoal
        value := badProof }
      match (← getEnv).toKernelEnv.addDecl options badDecl with
      | .error _ => pure ()
      | .ok _ => throwError "incorrect alias certificate accepted synchronously"
      logInfo "incorrect alias kernel certificate rejected"
#alias_kernel_probe
#print axioms AliasKernelProbe.checked
