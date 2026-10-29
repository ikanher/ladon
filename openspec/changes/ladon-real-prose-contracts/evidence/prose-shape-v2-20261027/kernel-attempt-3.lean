import Lean
open Lean Meta Elab Command
namespace AliasKernelProbe
def bump (n : Nat) : Nat := n + 7
def bad (n : Nat) : Nat := n + 8
end AliasKernelProbe

elab "#alias_kernel_probe" : command => do
  liftTermElabM do
    withLocalDeclD `n (mkConst ``Nat) fun n => do
      let original := mkApp (mkConst ``AliasKernelProbe.bump) n
      let canonical := mkApp2 (mkConst ``Nat.add) n (mkNatLit 7)
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
