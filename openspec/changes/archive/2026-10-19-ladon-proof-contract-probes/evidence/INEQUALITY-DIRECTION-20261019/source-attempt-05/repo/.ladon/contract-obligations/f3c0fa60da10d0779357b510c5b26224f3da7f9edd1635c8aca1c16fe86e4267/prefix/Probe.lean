import Lean
import Lean
import Std
namespace InequalityProbe
theorem nonnegative (_tag : Unit) : ∀ x : Nat, 0 ≤ x := by
  intro x
  exact Nat.zero_le x

run_cmd do
  let env ← Lean.getEnv
  if env.contains `InequalityProbe.use then throwError "parent declaration imported"
  if env.header.moduleNames.contains `Bridge then throwError "original source module imported"
theorem _root_.LadonContractPrefix_f3c0fa60da10d077 : _root_.True := by trivial
run_cmd do
  let count := (← Lean.Elab.Command.getScopes).length - 1
  for _ in List.range count do
    let scope ← Lean.Elab.Command.getScope
    if scope.header.isEmpty then
      Lean.Elab.Command.elabCommand (← `(command| end))
    else
      Lean.Elab.Command.elabCommand (← `(command| end $(Lean.mkIdent (Lean.Name.mkSimple scope.header))))
