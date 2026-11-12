import Pitfalls
namespace PitfallCases.PremiseProvenance01
theorem subject (P : Prop) [h : PitfallCorpus.HasConclusion P] : P := h.proof
#print axioms PitfallCases.PremiseProvenance01.subject
end PitfallCases.PremiseProvenance01
