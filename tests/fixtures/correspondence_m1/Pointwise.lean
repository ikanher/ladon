import Lean

namespace QuantifierFixture

theorem pointwise (_ : Nat) : ∀ n : Nat, ∃ k : Nat, n < k :=
  fun n => ⟨n + 1, Nat.lt_succ_self n⟩

theorem selected (d : Nat) : ∀ n : Nat, ∃ k : Nat, n < k := pointwise d

end QuantifierFixture
