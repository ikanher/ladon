import Pitfalls
namespace PitfallCases.OperationSemantics01
def subject : Prop := ∀ a b : Nat, ((a - b : Nat) : Int) = (a : Int) - (b : Int)
#print axioms PitfallCases.OperationSemantics01.subject
end PitfallCases.OperationSemantics01
