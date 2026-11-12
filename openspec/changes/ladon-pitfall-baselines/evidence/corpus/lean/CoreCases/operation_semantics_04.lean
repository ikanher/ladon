import Pitfalls
namespace PitfallCases.OperationSemantics04
theorem subject (a b : Nat) (h : b ≤ a) : a - b + b = a := by omega
#print axioms PitfallCases.OperationSemantics04.subject
end PitfallCases.OperationSemantics04
