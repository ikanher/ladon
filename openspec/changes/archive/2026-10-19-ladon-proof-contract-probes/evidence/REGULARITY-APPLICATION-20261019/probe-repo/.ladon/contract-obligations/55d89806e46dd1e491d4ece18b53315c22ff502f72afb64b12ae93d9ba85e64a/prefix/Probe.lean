import Lean
import Lean
import Std
namespace AppProbe
def M (_s _x : Nat) : Nat := 1
def N (s _x : Nat) : Nat := s
def F (x : Nat) : Nat := x
def C : Nat := 1
theorem weak (_tag : Unit) : ∀ s x : Nat, M s (F x) ≤ C * N (s + 1) x := by
  intro s x
  simp [M, N, F, C]

run_cmd do
  let env ← Lean.getEnv
  if env.contains `AppProbe.use then throwError "parent declaration imported"
  if env.header.moduleNames.contains `Bridge then throwError "original source module imported"
theorem _root_.LadonContractPrefix_55d89806e46dd1e4 : _root_.True := by trivial
run_cmd do
  let count := (← Lean.Elab.Command.getScopes).length - 1
  for _ in List.range count do
    let scope ← Lean.Elab.Command.getScope
    if scope.header.isEmpty then
      Lean.Elab.Command.elabCommand (← `(command| end))
    else
      Lean.Elab.Command.elabCommand (← `(command| end $(Lean.mkIdent (Lean.Name.mkSimple scope.header))))
