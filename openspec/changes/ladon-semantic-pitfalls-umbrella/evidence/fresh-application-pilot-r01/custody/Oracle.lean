import Mathlib.Order.Lattice.Nat
open Set
namespace PilotOracle

theorem fault : ¬ ∀ S : Set ℕ, sInf S ∈ S := by
  intro h
  have h0 := h (∅ : Set ℕ)
  simpa using h0

theorem control (a : ℕ) : sInf {n : ℕ | a ≤ n} ∈ {n : ℕ | a ≤ n} :=
  Nat.sInf_mem ⟨a, by simp⟩

#print axioms fault
#print axioms control
end PilotOracle
