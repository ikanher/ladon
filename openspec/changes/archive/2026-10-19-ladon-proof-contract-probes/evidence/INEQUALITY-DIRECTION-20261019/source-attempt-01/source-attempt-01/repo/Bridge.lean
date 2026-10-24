import Lean
import Std
namespace InequalityProbe
theorem nonnegative : ∀ x : Nat, 0 ≤ x := by
  intro x
  exact Nat.zero_le x
theorem use (_tag : Unit) : ∀ x : Nat, 0 ≤ x := nonnegative
end InequalityProbe
