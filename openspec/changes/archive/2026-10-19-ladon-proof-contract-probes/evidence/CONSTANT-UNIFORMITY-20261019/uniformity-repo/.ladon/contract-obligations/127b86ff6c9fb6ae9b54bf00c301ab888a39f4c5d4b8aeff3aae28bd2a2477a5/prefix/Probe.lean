import Lean
import Lean
import Std
namespace UniformProbe
def M (s _x : Nat) : Nat := s
def N (_s _x : Nat) : Nat := 1
def F (x : Nat) : Nat := x
theorem weak (_tag : Unit) : ∀ s : Nat, ∃ c : Nat, ∀ x : Nat,
    M s (F x) ≤ c * N (s + 0) x := by
  intro s
  refine ⟨s, ?_⟩
  intro x
  simp [M, N, F]

run_cmd do
  let env ← Lean.getEnv
  if env.contains `UniformProbe.use then throwError "parent declaration imported"
  if env.header.moduleNames.contains `Bridge then throwError "original source module imported"
theorem _root_.LadonContractPrefix_127b86ff6c9fb6ae : _root_.True := by trivial
run_cmd do
  let count := (← Lean.Elab.Command.getScopes).length - 1
  for _ in List.range count do
    let scope ← Lean.Elab.Command.getScope
    if scope.header.isEmpty then
      Lean.Elab.Command.elabCommand (← `(command| end))
    else
      Lean.Elab.Command.elabCommand (← `(command| end $(Lean.mkIdent (Lean.Name.mkSimple scope.header))))
