import Lean
import Std

namespace ObligationsRed

def N0 (s _x : Nat) : Nat := s
def N1 (s _x : Nat) : Nat := s
def N2 (s _x : Nat) : Nat := s
def N3 (s _x : Nat) : Nat := s

def F1 (x : Nat) : Nat := x + 1
def F2 (x : Nat) : Nat := x + 2
def F3 (x : Nat) : Nat := x + 3
def H (x : Nat) : Nat := F3 (F2 (F1 x))
def C : Nat := 1

theorem firstBound (s x : Nat) :
    N1 s (F1 x) ≤ C * N0 (s + 0) x := by
  simp [N0, N1, C]

theorem middleBound (s y : Nat) :
    N2 s (F2 y) ≤ C * N1 (s + 0) y := by
  simp [N1, N2, C]

theorem lastBound (s z : Nat) :
    N3 s (F3 z) ≤ C * N2 (s + 0) z := by
  simp [N2, N3, C]

theorem generatedRequirement (s : Nat) (y : Nat) :
    ObligationsRed.N2 s (ObligationsRed.F2 y) ≤ ObligationsRed.C * ObligationsRed.N1 (s + 1) y := by
  skip

run_cmd do
  let env ← Lean.getEnv
  unless (env.find? `ObligationsRed.threeStep).isNone do
    throwError "reserved parent declaration unexpectedly present"
  if env.header.moduleNames.contains `ObligationsRed then
    throwError "source module (which may contain the parent) was imported"

end ObligationsRed
