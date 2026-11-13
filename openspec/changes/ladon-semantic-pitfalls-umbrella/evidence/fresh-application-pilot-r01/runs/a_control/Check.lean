import Mathlib.Order.Lattice.Nat
open Set
#check Nat.sInf_mem
example (S : Set ℕ) (h : S.Nonempty) : sInf S ∈ S := Nat.sInf_mem h
example : ¬ (sInf (∅ : Set ℕ) ∈ (∅ : Set ℕ)) := by simp
example : sInf (∅ : Set ℕ) = 0 := by simp
