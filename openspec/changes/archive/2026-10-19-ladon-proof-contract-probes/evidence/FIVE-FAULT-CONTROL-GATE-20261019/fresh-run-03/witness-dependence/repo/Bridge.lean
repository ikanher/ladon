import Lean
import Std
namespace WitnessProbe
def P (w x : Nat) : Prop := x ≤ w
theorem weak (_tag : Unit) : ∀ x : Nat, ∃ w : Nat, P w x := by
  intro x
  exact ⟨x, Nat.le_refl _⟩
theorem use : ∀ x : Nat, ∃ w : Nat, P w x := weak ()
end WitnessProbe
