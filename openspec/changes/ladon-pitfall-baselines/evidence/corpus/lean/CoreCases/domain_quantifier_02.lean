import Pitfalls
namespace PitfallCases.DomainQuantifier02
def sourceClaim : Prop := ∀ z : Int, z + 0 = z
def subject : Prop := ∀ n : Nat, n + 0 = n
#print axioms PitfallCases.DomainQuantifier02.subject
end PitfallCases.DomainQuantifier02
