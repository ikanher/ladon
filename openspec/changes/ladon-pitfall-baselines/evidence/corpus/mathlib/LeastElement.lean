import Mathlib
namespace Audit.LeastElement

def p_e (n x1 x2 : Int) : Int := x1 + x2 - n

def B_e (n : Nat) : Prop :=
  ∀ (x1 x2 : Nat), p_e (n : Int) (x1 : Int) (x2 : Int) ≠ 0

noncomputable def n_e : Nat := sInf {n : Nat | B_e n}
noncomputable def r_e : Rat := 1 / (n_e + 1)

-- Operational subjects are propositions only. Validation proofs live in Validation.lean.
def case_existence_defaults_01 : Prop := n_e ∈ {n : Nat | B_e n}
def case_existence_defaults_02 : Prop := ∃ n : Nat, B_e n
def case_existence_defaults_03 : Prop :=
  ∀ S : Set ℕ, S.Nonempty → sInf S ∈ S ∧ ∀ n ∈ S, sInf S ≤ n
def case_existence_defaults_04 : Prop := n_e = 0
end Audit.LeastElement
