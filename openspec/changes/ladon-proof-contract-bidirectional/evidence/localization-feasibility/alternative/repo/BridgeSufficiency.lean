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


end ObligationsRed

theorem bridgeIsSufficient (s x : Nat)
    (h : ObligationsRed.N2 s (ObligationsRed.F2 (ObligationsRed.F1 x)) ≤
      ObligationsRed.C * ObligationsRed.N1 (s + 0) (ObligationsRed.F1 x)) :
    ObligationsRed.N3 s (ObligationsRed.H x) ≤
      ObligationsRed.C * ObligationsRed.N0 (s + 0) x := by
  calc
    ObligationsRed.N3 s (ObligationsRed.H x) ≤
        ObligationsRed.C * ObligationsRed.N2 (s + 0)
          (ObligationsRed.F2 (ObligationsRed.F1 x)) := by
      simpa [ObligationsRed.H] using
        ObligationsRed.lastBound s (ObligationsRed.F2 (ObligationsRed.F1 x))
    _ = ObligationsRed.N2 s (ObligationsRed.F2 (ObligationsRed.F1 x)) := by
      simp [ObligationsRed.N2, ObligationsRed.C]
    _ ≤ ObligationsRed.C * ObligationsRed.N1 (s + 0) (ObligationsRed.F1 x) := h
    _ = ObligationsRed.N1 s (ObligationsRed.F1 x) := by
      simp [ObligationsRed.N1, ObligationsRed.C]
    _ ≤ ObligationsRed.C * ObligationsRed.N0 (s + 0) x :=
      ObligationsRed.firstBound s x
