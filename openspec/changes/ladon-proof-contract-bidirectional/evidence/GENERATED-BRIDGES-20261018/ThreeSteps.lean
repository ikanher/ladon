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

theorem secondBound (s x : Nat) :
    N2 s (F2 x) ≤ C * N1 (s + 2) x := by
  simp [N1, N2, C]

theorem thirdBound (s x : Nat) :
    N3 s (F3 x) ≤ C * N2 (s + 0) x := by
  simp [N2, N3, C]

theorem alternateBound (s x : Nat) :
    N3 s (H x) ≤ C * N0 (s + 0) x := by
  simp [N0, N3, C]

theorem endpoint (s x : Nat) :
    N3 s (H x) ≤ C * N0 (s + 0) x := by
  exact alternateBound s x

end ThreeSteps
