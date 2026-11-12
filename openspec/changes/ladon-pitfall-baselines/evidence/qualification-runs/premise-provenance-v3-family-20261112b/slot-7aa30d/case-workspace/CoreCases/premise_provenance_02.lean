import Pitfalls
namespace PitfallCases.PremiseProvenance02
theorem subject (P : Prop) (h : PitfallCorpus.HasConclusion P) : P := h.proof
#print axioms PitfallCases.PremiseProvenance02.subject
end PitfallCases.PremiseProvenance02
