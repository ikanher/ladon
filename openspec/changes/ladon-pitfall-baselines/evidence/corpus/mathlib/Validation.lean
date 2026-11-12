import ExistenceCases.Case01
import ExistenceCases.Case02
import ExistenceCases.Case03
import ExistenceCases.Case04
namespace Audit.LeastElement.Validation
open Audit.LeastElement

theorem every_n_has_root (n : ℕ) : p_e (n : Int) (n : Int) 0 = 0 := by simp [p_e]
theorem no_B_e (n : ℕ) : ¬ B_e n := by
  intro h
  have bad := h n 0
  simp [p_e] at bad
theorem defining_set_empty : {n : ℕ | B_e n} = ∅ := by ext n; simp [no_B_e]
theorem no_witness : ¬ ∃ n, B_e n := by simp [no_B_e]
theorem default_n : n_e = 0 := by rw [n_e, defining_set_empty, Nat.sInf_empty]
theorem oracle_existence_defaults_01 : ¬ ExistenceCases.Case01.subject := by
  change n_e ∉ {n : Nat | B_e n}; rw [default_n]; exact no_B_e 0
theorem oracle_existence_defaults_02 : ¬ ExistenceCases.Case02.subject := by
  change ¬ ∃ n, B_e n; exact no_witness
theorem validates_case_03 : ExistenceCases.Case03.subject := by
  intro S hS; exact ⟨Nat.sInf_mem hS, fun n hn => Nat.sInf_le hn⟩
theorem validates_case_04 : ExistenceCases.Case04.subject := by change n_e=0; exact default_n

#print axioms oracle_existence_defaults_01
#print axioms oracle_existence_defaults_02
#print axioms validates_case_03
#print axioms validates_case_04
end Audit.LeastElement.Validation
