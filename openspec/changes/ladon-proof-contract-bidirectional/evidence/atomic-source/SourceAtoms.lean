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

theorem parent (s x : Nat) :
    B s (F x) ≤ C * A (s + 3) x := by
  simp [A, B, C]

end SourceAtoms
