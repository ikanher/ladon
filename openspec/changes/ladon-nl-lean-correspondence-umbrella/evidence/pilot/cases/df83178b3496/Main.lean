import Lean

theorem result (a b c : Nat) (h₁ : a ≤ b) (h₂ : b ≤ c) : a ≤ c := by
  exact Nat.le_trans h₁ h₂
