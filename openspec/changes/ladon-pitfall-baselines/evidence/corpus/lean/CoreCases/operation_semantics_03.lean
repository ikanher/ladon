import Pitfalls
namespace PitfallCases.OperationSemantics03
theorem subject : ∀ n : Nat, n + 0 = n := by intro n; omega
#print axioms PitfallCases.OperationSemantics03.subject
end PitfallCases.OperationSemantics03
