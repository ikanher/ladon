import Lean
namespace PitfallCorpus

def Pointwise : Prop := ∀ n : Nat, ∃ k : Nat, n < k
theorem pointwise_true : Pointwise := by
  intro n
  exact ⟨n + 1, Nat.lt_succ_self n⟩
def Uniform : Prop := ∃ k : Nat, ∀ n : Nat, n < k
theorem uniform_false : ¬ Uniform := by
  rintro ⟨k, hk⟩
  exact Nat.lt_irrefl k (hk k)
theorem nat_domain_control : ∀ n : Nat, n + 0 = n := by intro n; omega
def NatIntMismatch : Prop := (2 : Nat) - 3 = 0 ∧ (Int.ofNat 2 - 3 : Int) = -1
theorem nat_int_mismatch : NatIntMismatch := by
  constructor <;> decide

def Contradictory (n : Nat) : Prop := n = 0 ∧ n = 1
theorem contradictory_inconsistent : ¬ ∃ n, Contradictory n := by
  rintro ⟨n, h0, h1⟩
  have : (0 : Nat) = 1 := h0.symm.trans h1
  exact Nat.zero_ne_one this
theorem inhabited_control : ∃ n : Nat, n = 2 := ⟨2, rfl⟩
theorem impossible_branch_control (h : False) : True := h.elim

class HasConclusion (P : Prop) : Prop where
  proof : P
theorem conclusion_from_instance (P : Prop) [h : HasConclusion P] : P := h.proof
theorem explicit_conditional_control (P : Prop) (h : P) : P := h

def EmptySet : Nat → Prop := fun _ => False
def Selector := Nat
 def selectedProperty : Selector → Prop := fun n => EmptySet n
theorem empty_selector_failure : ¬ ∃ n : Nat, selectedProperty n := by
  rintro ⟨n, h⟩
  exact h

def NonemptySet : Nat → Prop := fun n => n = 4
theorem nonempty_witness_control : ∃ n : Nat, NonemptySet n := ⟨4, rfl⟩
noncomputable def Defaulted (p : Prop) : Nat := by
  classical
  exact if h : ∃ n, p then Classical.choose h else 0
theorem default_is_total : ∀ p, ∃ n, n = Defaulted p := by
  classical
  intro p
  exact ⟨Defaulted p, rfl⟩

theorem hypothesis_strengthened_control (n : Nat) (h : n = 0) : n = 0 := h
theorem unchanged_goal_control (n : Nat) : n = n := rfl
axiom supplied_axiom : True
theorem axiom_dependency_control : True := supplied_axiom

theorem guarded_subtraction_control (a b : Nat) (h : b ≤ a) : a - b + b = a := by omega
theorem representation_control (n : Fin 5) : n.val < 5 := n.isLt

theorem fixed_parameter_control (n : Nat) : ∃ k : Nat, k = n := ⟨n, rfl⟩
theorem independent_provider_control : 2 + 2 = 4 := by decide

-- Unique case-owned declarations; each corpus row has its own Lean subject.
def case_domain_quantifier_01 : Prop := Uniform
theorem oracle_domain_quantifier_01 : ¬ case_domain_quantifier_01 := uniform_false
def case_domain_quantifier_02_source : Prop := ∀ z : Int, z + 0 = z
def case_domain_quantifier_02_formal : Prop := ∀ n : Nat, n + 0 = n
theorem case_domain_quantifier_03 (n : Fin 5) : n.val < 5 := representation_control n
theorem case_domain_quantifier_04 : Pointwise := pointwise_true
def case_assumption_feasibility_01 : Prop := ∃ n, Contradictory n
theorem oracle_assumption_feasibility_01 : ¬ case_assumption_feasibility_01 := contradictory_inconsistent
def case_assumption_feasibility_02 : Prop := ∃ n : Nat, n > 0 ∧ n = 0
theorem oracle_assumption_feasibility_02 : ¬ case_assumption_feasibility_02 := by
  rintro ⟨n, hpos, hzero⟩
  omega
theorem case_assumption_feasibility_03 (h : False) : True := impossible_branch_control h
theorem case_assumption_feasibility_04 (n : Nat) : ∃ k : Nat, k = n := fixed_parameter_control n
theorem case_premise_provenance_01 (P : Prop) [h : HasConclusion P] : P := conclusion_from_instance P
theorem case_premise_provenance_02 (P : Prop) (h : HasConclusion P) : P := h.proof
theorem case_premise_provenance_03 (P : Prop) (h : P) : P := h
theorem case_premise_provenance_04 : 2 + 2 = 4 := by decide
theorem case_operation_semantics_01 : NatIntMismatch := nat_int_mismatch
def case_operation_semantics_02 : Prop := ∀ a b : Nat, a - b + b = a
theorem oracle_operation_semantics_02 : ¬ case_operation_semantics_02 := by
  intro h
  have bad := h 2 3
  omega
theorem case_operation_semantics_03 : ∀ n : Nat, n + 0 = n := nat_domain_control
theorem case_operation_semantics_04 (a : Nat) : a - 0 = a := by simp
def case_claim_trust_01 : Prop := ∀ n : Nat, n = 0 → n = 0
theorem oracle_claim_trust_01 : ¬ (∀ n : Nat, n = 0) := by
  intro h
  have := h 1
  omega
theorem case_claim_trust_02 : True := supplied_axiom
theorem case_claim_trust_03 (n : Nat) : n = n := rfl
theorem case_claim_trust_04 : 2 + 2 = 4 := by decide


-- Per-case trust inventory for the current corpus draft.
#print axioms case_domain_quantifier_01
#print axioms case_domain_quantifier_02_source
#print axioms case_domain_quantifier_02_formal
#print axioms oracle_domain_quantifier_01
#print axioms case_domain_quantifier_02_formal
#print axioms case_domain_quantifier_03
#print axioms case_domain_quantifier_04
#print axioms case_assumption_feasibility_01
#print axioms oracle_assumption_feasibility_01
#print axioms case_assumption_feasibility_02
#print axioms oracle_assumption_feasibility_02
#print axioms case_assumption_feasibility_03
#print axioms case_assumption_feasibility_04
#print axioms case_premise_provenance_01
#print axioms case_premise_provenance_02
#print axioms case_premise_provenance_03
#print axioms case_premise_provenance_04
#print axioms case_operation_semantics_01
#print axioms case_operation_semantics_02
#print axioms oracle_operation_semantics_02
#print axioms case_operation_semantics_03
#print axioms case_operation_semantics_04
#print axioms case_claim_trust_01
#print axioms oracle_claim_trust_01
#print axioms case_claim_trust_02
#print axioms case_claim_trust_03
#print axioms case_claim_trust_04

end PitfallCorpus
