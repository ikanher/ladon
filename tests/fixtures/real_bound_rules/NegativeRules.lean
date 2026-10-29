import LadonRealBoundComposition
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Linarith

open Ladon.RealBound
namespace RuleControls

theorem negative_multiplier : (-1 : Real) ≤ 0 ∧ ¬ ((-1 : Real) * (-1) ≤ (-1 : Real) * 0) := by
  norm_num

theorem negative_input_bound : (0 : Real) ≤ 1 ∧ ¬ ((0 : Real) * (-1) ≤ (1 : Real) * (-1)) := by
  norm_num

theorem pointwise_not_uniform :
    (∀ a : Real, 0 ≤ a → ∃ K : Real, 0 ≤ K ∧ a ≤ K) ∧
      ¬ (∃ K : Real, 0 ≤ K ∧ ∀ a : Real, 0 ≤ a → a ≤ K) := by
  constructor
  · intro a ha
    exact ⟨a, ha, le_refl a⟩
  · rintro ⟨K, hK, uniform⟩
    have h := uniform (K + 1) (by linarith)
    linarith

section Mismatches
variable {X Y Z P : Type} {J : X → Set P → Nat → Real → Prop}
  {Q Q' : Y → Set P → Nat → Real → Prop} {R : Z → Set P → Nat → Real → Prop}
  {x : X} {y y' : Y} {z : Z} {S S' : Set P} {a b b' c : Nat} {C D K L : Real}

theorem changed_predicate (first : TransferAt J Q x y S a b C K)
    (second : TransferAt Q' R y z S b c (K * C) L) : True := by
  fail_if_success have := transfer_compose first second
  trivial

theorem changed_set (first : TransferAt J Q x y S a b C K)
    (second : TransferAt Q R y z S' b c (K * C) L) : True := by
  fail_if_success have := transfer_compose first second
  trivial

theorem changed_order (first : TransferAt J Q x y S a b C K)
    (second : TransferAt Q R y z S b' c (K * C) L) : True := by
  fail_if_success have := transfer_compose first second
  trivial

theorem changed_object (first : TransferAt J Q x y S a b C K)
    (second : TransferAt Q R y' z S b c (K * C) L) : True := by
  fail_if_success have := transfer_compose first second
  trivial

theorem changed_bound (first : TransferAt J Q x y S a b C K)
    (second : TransferAt Q R y z S b c D L) : True := by
  fail_if_success have := transfer_compose first second
  trivial

theorem missing_sign (h : C ≤ D) : True := by
  fail_if_success have : K * C ≤ K * D := scaled_bound_mono h
  trivial

theorem missing_prefix (first : TransferAt J Q x y S a b C K) : True := by
  fail_if_success have : TransferAt J Q x y S (a + 1) b C K :=
    transfer_input_prefix (Nat.le_succ a) first
  trivial

end Mismatches
end RuleControls
