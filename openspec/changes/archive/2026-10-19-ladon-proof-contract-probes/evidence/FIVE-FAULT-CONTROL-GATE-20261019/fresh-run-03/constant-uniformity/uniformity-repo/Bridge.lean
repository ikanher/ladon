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
theorem use : ∀ s : Nat, ∃ c : Nat, ∀ x : Nat,
    M s (F x) ≤ c * N (s + 0) x := weak ()
end UniformProbe
