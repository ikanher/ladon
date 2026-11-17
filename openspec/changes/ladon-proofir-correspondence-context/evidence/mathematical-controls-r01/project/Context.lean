import Lean

namespace ContextFixture

def shifted (i : Fin 5) : Nat := i.val + 5

theorem bridge (n : Nat) (h : n < 5) : n < 5 := h
theorem selected (n : Nat) (h : n < 5) : n < 5 := bridge n h

theorem original_source : ∀ i : Fin 5, i.val < 5 := fun i => i.isLt

theorem pointwise (_ : Nat) : ∀ n : Nat, ∃ k : Nat, n < k :=
  fun n => ⟨n + 1, Nat.lt_succ_self n⟩
theorem selectedPointwise (d : Nat) : ∀ n : Nat, ∃ k : Nat, n < k := pointwise d

#print axioms original_source
#print axioms selected
#print axioms selectedPointwise
end ContextFixture
