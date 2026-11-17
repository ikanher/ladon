import Lean

-- The exact attributed uniform proposition, separate from its transfer route.
theorem uniform_source_false : ¬ (∀ d : Nat, ∃ k : Nat, ∀ n : Nat, n < k) := by
  intro h
  obtain ⟨k, hk⟩ := h 0
  exact Nat.lt_irrefl k (hk k)

#print axioms uniform_source_false
