import Lean
import Std
namespace DomainProbe
def P (x : Nat) : Prop := x = 0
theorem guarded (_tag : Unit) : ∀ x : Nat, x ≤ 0 → P x := by
  intro x hx
  dsimp [P]
  exact Nat.le_zero.mp hx
theorem use : ∀ x : Nat, x ≤ 0 → P x := guarded ()
end DomainProbe
