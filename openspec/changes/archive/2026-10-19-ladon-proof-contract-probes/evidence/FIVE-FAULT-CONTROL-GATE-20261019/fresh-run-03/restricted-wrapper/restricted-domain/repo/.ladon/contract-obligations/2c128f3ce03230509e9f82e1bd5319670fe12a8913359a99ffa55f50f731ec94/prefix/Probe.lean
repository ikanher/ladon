import Lean
import Lean
import Std
namespace DomainProbe
def P (x : Nat) : Prop := x = 0
theorem guarded (_tag : Unit) : ∀ x : Nat, x ≤ 0 → P x := by
  intro x hx
  dsimp [P]
  exact Nat.le_zero.mp hx

run_cmd do
  let env ← Lean.getEnv
  if env.contains `DomainProbe.use then throwError "parent declaration imported"
  if env.header.moduleNames.contains `Bridge then throwError "original source module imported"
theorem _root_.LadonContractPrefix_2c128f3ce0323050 : _root_.True := by trivial
run_cmd do
  let count := (← Lean.Elab.Command.getScopes).length - 1
  for _ in List.range count do
    let scope ← Lean.Elab.Command.getScope
    if scope.header.isEmpty then
      Lean.Elab.Command.elabCommand (← `(command| end))
    else
      Lean.Elab.Command.elabCommand (← `(command| end $(Lean.mkIdent (Lean.Name.mkSimple scope.header))))
