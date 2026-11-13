import Mathlib.Tactic.NormNum

/- Unscored, supplied rational abstractions. The stochastic source embedding is
reviewed separately; these certificates do not formalize that embedding. -/
namespace PitfallsDevelopment

def OriginalOneStep (x0 x1 a : ℚ) : Prop :=
  0 ≤ x0 ∧ 0 ≤ x1 ∧ 0 ≤ a ∧ x1 ≤ (1 + a) * x0

def NormalizedAccount (x0 x1 a : ℚ) : Prop := x1 / (1 + a) ≤ x0

def MutatedAccount (x0 x1 : ℚ) : Prop := x1 ≤ x0

theorem faithful : OriginalOneStep 1 2 1 ∧ NormalizedAccount 1 2 1 := by
  norm_num [OriginalOneStep, NormalizedAccount]

theorem counterexample : ∃ x0 x1 a : ℚ,
    OriginalOneStep x0 x1 a ∧ NormalizedAccount x0 x1 a ∧
      ¬ MutatedAccount x0 x1 := by
  refine ⟨1, 2, 1, ?_⟩
  norm_num [OriginalOneStep, NormalizedAccount, MutatedAccount]

theorem outside_assumptions : ¬ OriginalOneStep (-1) (-2) 1 := by
  norm_num [OriginalOneStep]

end PitfallsDevelopment
