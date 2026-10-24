import Lean
import Std

namespace SourceAtoms

def A (s _x : Nat) : Nat := s
def B (s _x : Nat) : Nat := s
def F (x : Nat) : Nat := x + 1
def C : Nat := 1
def D : Nat := 2

theorem provider (s x : Nat) :
    B s (F x) ≤ C * A (s + 0) x := by
  simp [A, B, C]

theorem providerD (s x : Nat) :
    B s (F x) ≤ D * A (s + 0) x := by
  simp [A, B, D, Nat.two_mul]


run_cmd do
  let env ← Lean.getEnv
  if env.contains `SourceAtoms.parent then throwError "parent declaration imported"
  if env.header.moduleNames.contains `SourceAtoms then throwError "original source module imported"
theorem _root_.LadonContractPrefix_8790f0401b48fb5f : _root_.True := by trivial
run_cmd do
  let count := (← Lean.Elab.Command.getScopes).length - 1
  for _ in List.range count do
    let scope ← Lean.Elab.Command.getScope
    if scope.header.isEmpty then
      Lean.Elab.Command.elabCommand (← `(command| end))
    else
      Lean.Elab.Command.elabCommand (← `(command| end $(Lean.mkIdent (Lean.Name.mkSimple scope.header))))
