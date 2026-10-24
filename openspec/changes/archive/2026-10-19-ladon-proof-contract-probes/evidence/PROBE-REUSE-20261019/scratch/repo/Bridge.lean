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
theorem use : ∀ s x : Nat, M s (F x) ≤ C * N (s + 1) x := weak ()
end AppProbe
