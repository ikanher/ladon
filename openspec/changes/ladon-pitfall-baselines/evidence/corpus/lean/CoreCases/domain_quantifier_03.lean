import Pitfalls
namespace PitfallCases.DomainQuantifier03
theorem subject : ∀ n : Nat, n < 5 → ∃ i : Fin 5, i.val = n := by
  intro n hn
  exact ⟨⟨n, hn⟩, rfl⟩
#print axioms PitfallCases.DomainQuantifier03.subject
end PitfallCases.DomainQuantifier03
