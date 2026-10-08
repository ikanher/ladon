import Mathlib
namespace Audit.LeastElement
-- Namespaced transcription of the displayed definitions and ring theorem.
def p_e (n x1 x2 : Int) : Int := x1 + x2 - n

def B_e (n : Nat) : Prop :=
forall (x1 x2 : Nat), p_e (n : Int) (x1 : Int) (x2 : Int) != 0

noncomputable def n_e : Nat := sInf {n : Nat | B_e n}
noncomputable def r_e : Rat := 1 / (n_e + 1)
theorem example_3_1 : (r_e + 1) ^ 2 = r_e ^ 2 + 2 * r_e + 1 := by ring

-- Independent existence checks, absent from the original algebraic theorem.
theorem every_n_has_root (n : ℕ) : p_e (n : Int) (n : Int) 0 = 0 := by
  simp [p_e]
theorem no_B_e (n : ℕ) : ¬ B_e n := by
  intro h
  exact h n 0 (every_n_has_root n)
theorem defining_set_empty : {n : ℕ | B_e n} = ∅ := by
  ext n
  simp [no_B_e]
theorem no_witness : ¬ ∃ n, B_e n := by
  simp [no_B_e]
theorem default_n : n_e = 0 := by
  rw [n_e, defining_set_empty, Nat.sInf_empty]
theorem default_r : r_e = 1 := by
  simp [r_e, default_n]

-- A faithful conditional rendering: nonemptiness is explicit, not proved for B_e.
theorem conditional_least (S : Set ℕ) (hS : S.Nonempty) :
    sInf S ∈ S ∧ ∀ n ∈ S, sInf S ≤ n := by
  exact ⟨Nat.sInf_mem hS, fun n hn => Nat.sInf_le hn⟩
theorem conditional_algebra (S : Set ℕ) (hS : S.Nonempty) :
    sInf S ∈ S ∧
    (1 / ((sInf S : ℚ) + 1) + 1)^2 =
      (1 / ((sInf S : ℚ) + 1))^2 + 2*(1 / ((sInf S : ℚ) + 1)) + 1 := by
  exact ⟨(conditional_least S hS).1, by ring⟩
#print axioms example_3_1
#print axioms every_n_has_root
#print axioms no_B_e
#print axioms defining_set_empty
#print axioms no_witness
#print axioms default_n
#print axioms default_r
#print axioms conditional_least
#print axioms conditional_algebra
end Audit.LeastElement
