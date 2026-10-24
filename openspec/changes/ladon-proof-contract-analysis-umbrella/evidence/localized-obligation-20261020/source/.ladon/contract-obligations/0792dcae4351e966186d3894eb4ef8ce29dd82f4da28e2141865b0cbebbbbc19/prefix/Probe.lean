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


run_cmd do
  let env ← Lean.getEnv
  if env.contains `ThreeSteps.firstBound then throwError "parent declaration imported"
  if env.header.moduleNames.contains `ThreeSteps then throwError "original source module imported"
theorem _root_.LadonContractPrefix_0792dcae4351e966 : _root_.True := by trivial
run_cmd do
  let count := (← Lean.Elab.Command.getScopes).length - 1
  for _ in List.range count do
    let scope ← Lean.Elab.Command.getScope
    if scope.header.isEmpty then
      Lean.Elab.Command.elabCommand (← `(command| end))
    else
      Lean.Elab.Command.elabCommand (← `(command| end $(Lean.mkIdent (Lean.Name.mkSimple scope.header))))
