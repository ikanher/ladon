import Pitfalls
namespace PitfallCases.AssumptionFeasibility04
theorem subject (n : Nat) : ∃ k : Nat, k = n := ⟨n, rfl⟩
#print axioms PitfallCases.AssumptionFeasibility04.subject
end PitfallCases.AssumptionFeasibility04
