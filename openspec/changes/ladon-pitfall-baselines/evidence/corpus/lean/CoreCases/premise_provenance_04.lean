import Pitfalls
namespace PitfallCases.PremiseProvenance04
theorem arithmeticFact : 2 + 2 = 4 := by decide
def provider : PitfallCorpus.HasConclusion (2 + 2 = 4) := ⟨arithmeticFact⟩
theorem subject : 2 + 2 = 4 := provider.proof
#print axioms PitfallCases.PremiseProvenance04.subject
end PitfallCases.PremiseProvenance04
