import Mf.DP.OptimalSubsamplingLaw

namespace Mf
namespace DP
namespace OptimalSubsampling

noncomputable section

/-!
# Fixed-cardinality sampling-law surface

This owner refines the common expected-count family by requiring every
positive-mass participation subset to have cardinality exactly `k`. The
restriction excludes concentrated count-varying laws while retaining
nonuniform laws on the `k`-subsets.
-/

/-- An expected-count law supported entirely on participation subsets of size `k`. -/
structure FixedCardinalitySamplingLaw (T k : ℕ)
    extends IndependentExampleSamplingLaw T k where
  support_card_eq :
    ∀ s : Finset (Fin T),
      0 < toIndependentExampleSamplingLaw.mass s →
        s.card = k

/-- Uniform BIS, embedded in the fixed-cardinality family. -/
def bisFixedCardinalitySamplingLaw
    (T k : ℕ) (hk : k ≤ T) :
    FixedCardinalitySamplingLaw T k where
  toIndependentExampleSamplingLaw := bisSamplingLaw T k hk
  support_card_eq :=
    (countDeviation_eq_zero_iff_positive_mass_card_eq
      (bisSamplingLaw T k hk)).mp
      (bis_countDeviation_minimal hk (bisSamplingLaw T k hk)).2

/-- Every fixed-cardinality law has zero participation-count deviation. -/
theorem fixedCardinality_countDeviation_eq_zero
    {T k : ℕ}
    (law : FixedCardinalitySamplingLaw T k) :
    law.toIndependentExampleSamplingLaw.countDeviation = 0 :=
  (countDeviation_eq_zero_iff_positive_mass_card_eq
    law.toIndependentExampleSamplingLaw).mpr law.support_card_eq

end

end OptimalSubsampling
end DP
end Mf
