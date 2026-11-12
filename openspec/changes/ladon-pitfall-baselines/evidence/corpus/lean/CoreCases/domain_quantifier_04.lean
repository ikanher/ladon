import Pitfalls
namespace PitfallCases.DomainQuantifier04
theorem subject : PitfallCorpus.Pointwise := by
  intro n
  exact ⟨n + 1, Nat.lt_succ_self n⟩
#print axioms PitfallCases.DomainQuantifier04.subject
end PitfallCases.DomainQuantifier04
