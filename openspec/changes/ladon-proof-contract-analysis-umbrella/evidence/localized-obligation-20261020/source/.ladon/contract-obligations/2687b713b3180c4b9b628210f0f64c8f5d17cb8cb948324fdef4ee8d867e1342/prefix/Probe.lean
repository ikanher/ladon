import Lean
import Lean
import Std

namespace ThreeSteps

def N0 (s _x : Nat) : Nat := s
def N1 (s _x : Nat) : Nat := s
def N2 (s _x : Nat) : Nat := s + 2
def N3 (_s _x : Nat) : Nat := 0

def F1 (x : Nat) : Nat := x + 1
def F2 (x : Nat) : Nat := x + 2
def F3 (x : Nat) : Nat := x + 3
def G (x : Nat) : Nat := F2 (F1 x)
def H (x : Nat) : Nat := F3 (G x)
def C : Nat := 1

theorem firstBound (s x : Nat) :
    N1 s (F1 x) ≤ C * N0 (s + 0) x := by
  simp [N0, N1, C]


run_cmd do
  let env ← Lean.getEnv
  if env.contains `ThreeSteps.secondBound then throwError "parent declaration imported"
  if env.header.moduleNames.contains `ThreeSteps then throwError "original source module imported"
theorem _root_.LadonContractPrefix_a667bc09768f521c : _root_.True := by trivial
run_cmd do
  let count := (← Lean.Elab.Command.getScopes).length - 1
  for _ in List.range count do
    let scope ← Lean.Elab.Command.getScope
    if scope.header.isEmpty then
      Lean.Elab.Command.elabCommand (← `(command| end))
    else
      Lean.Elab.Command.elabCommand (← `(command| end $(Lean.mkIdent (Lean.Name.mkSimple scope.header))))

run_cmd do
  let env ← Lean.getEnv
  if env.contains `ThreeSteps.endpoint then throwError "parent declaration imported"
  if env.header.moduleNames.contains `ThreeSteps then throwError "original source module imported"
theorem _root_.LadonContractPrefix_2687b713b3180c4b : _root_.True := by trivial
run_cmd do
  let count := (← Lean.Elab.Command.getScopes).length - 1
  for _ in List.range count do
    let scope ← Lean.Elab.Command.getScope
    if scope.header.isEmpty then
      Lean.Elab.Command.elabCommand (← `(command| end))
    else
      Lean.Elab.Command.elabCommand (← `(command| end $(Lean.mkIdent (Lean.Name.mkSimple scope.header))))
