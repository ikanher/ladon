import Lean
import Lean
import Std
namespace WitnessProbe
def P (w x : Nat) : Prop := x ≤ w
theorem weak (_tag : Unit) : ∀ x : Nat, ∃ w : Nat, P w x := by
  intro x
  exact ⟨x, Nat.le_refl _⟩

run_cmd do
  let env ← Lean.getEnv
  if env.contains `WitnessProbe.use then throwError "parent declaration imported"
  if env.header.moduleNames.contains `Bridge then throwError "original source module imported"
theorem _root_.LadonContractPrefix_7caa8b0005b3e1fa : _root_.True := by trivial
run_cmd do
  let count := (← Lean.Elab.Command.getScopes).length - 1
  for _ in List.range count do
    let scope ← Lean.Elab.Command.getScope
    if scope.header.isEmpty then
      Lean.Elab.Command.elabCommand (← `(command| end))
    else
      Lean.Elab.Command.elabCommand (← `(command| end $(Lean.mkIdent (Lean.Name.mkSimple scope.header))))
