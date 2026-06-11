namespace Bench

theorem alpha_nonneg (n : Nat) : 0 <= n := by
  exact Nat.zero_le n

theorem beta_nonneg (n : Nat) : 0 <= n := by
  exact Nat.zero_le n

theorem gamma_ge_one (n : Nat) (h : 1 <= n) : 1 <= n := by
  exact h

theorem delta_ge_one (n : Nat) (h : 1 <= n) : 1 <= n := by
  exact h

end Bench
