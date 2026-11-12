import CoreCases.assumption_feasibility_01
import CoreCases.assumption_feasibility_02
import CoreCases.assumption_feasibility_03
import CoreCases.assumption_feasibility_04
import CoreCases.claim_trust_01
import CoreCases.claim_trust_02
import CoreCases.claim_trust_03
import CoreCases.claim_trust_04
import CoreCases.domain_quantifier_01
import CoreCases.domain_quantifier_02
import CoreCases.domain_quantifier_03
import CoreCases.domain_quantifier_04
import CoreCases.operation_semantics_01
import CoreCases.operation_semantics_02
import CoreCases.operation_semantics_03
import CoreCases.operation_semantics_04
import CoreCases.premise_provenance_01
import CoreCases.premise_provenance_02
import CoreCases.premise_provenance_03
import CoreCases.premise_provenance_04
namespace PitfallCorpus.Validation
open PitfallCorpus

theorem oracle_domain_quantifier_01 : ¬ PitfallCases.DomainQuantifier01.subject := by
  rintro ⟨k, hk⟩; exact Nat.lt_irrefl k (hk k)
theorem oracle_assumption_feasibility_01 : ¬ PitfallCases.AssumptionFeasibility01.subject := by
  rintro ⟨n, h0, h1⟩; have h : (0 : Nat) = 1 := h0.symm.trans h1; exact Nat.zero_ne_one h
theorem oracle_assumption_feasibility_02 : ¬ PitfallCases.AssumptionFeasibility02.subject := by
  rintro ⟨n, hp, hz⟩; omega
theorem oracle_operation_semantics_01 : ¬ PitfallCases.OperationSemantics01.subject := by
  intro h
  have bad := h 2 3
  have hne : ((2 - 3 : Nat) : Int) ≠ (2 : Int) - 3 := by decide
  exact hne bad
theorem oracle_operation_semantics_02 : ¬ PitfallCases.OperationSemantics02.subject := by
  intro h; have bad := h 2 3; omega
theorem oracle_claim_trust_01 : ¬ (∀ n : Nat, n = 0) := by intro h; have := h 1; omega

#print axioms oracle_domain_quantifier_01
#print axioms oracle_assumption_feasibility_01
#print axioms oracle_assumption_feasibility_02
#print axioms oracle_operation_semantics_01
#print axioms oracle_operation_semantics_02
#print axioms oracle_claim_trust_01
end PitfallCorpus.Validation
