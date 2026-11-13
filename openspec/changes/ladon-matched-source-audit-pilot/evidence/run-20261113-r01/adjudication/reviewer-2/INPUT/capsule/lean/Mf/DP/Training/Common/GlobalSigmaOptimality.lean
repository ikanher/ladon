import Mf.DP.GaussianApproxDP

namespace Mf
namespace DP
namespace Training

open MeasureTheory

noncomputable section

/-!
# Uniform global sigma optimality

This module owns only the family-independent meaning of a globally least
positive Gaussian scale. Domain-specific modules must still prove that their
privacy predicate has this shape. In particular, these definitions do not
turn a finite candidate minimum or an unattained infimum into an optimum.
-/

/-- Uniform privacy at one positive real noise scale for a public oracle family. -/
def UniformPrivateAt
    {Oracle Dataset Output : Type}
    [MeasurableSpace Output]
    (adj : Dataset → Dataset → Prop)
    (mechanism : Oracle → ℝ → Dataset → Measure Output)
    (epsilon delta sigma : ℝ) : Prop :=
  0 < sigma ∧
    ∀ oracle, ApproxDP adj (mechanism oracle sigma) epsilon delta

/--
`sigmaStar` is the attained global threshold exactly when the feasible positive
scales form the upper ray beginning at `sigmaStar`.
-/
def IsGlobalSigmaThreshold
    (privateAt : ℝ → Prop)
    (sigmaStar : ℝ) : Prop :=
  0 < sigmaStar ∧
    privateAt sigmaStar ∧
    ∀ sigma, 0 < sigma → (privateAt sigma ↔ sigmaStar ≤ sigma)

/-- Existence of an attained globally least positive sigma. -/
def HasGlobalSigmaThreshold (privateAt : ℝ → Prop) : Prop :=
  ∃ sigmaStar, IsGlobalSigmaThreshold privateAt sigmaStar

namespace IsGlobalSigmaThreshold

theorem positive
    {privateAt : ℝ → Prop} {sigmaStar : ℝ}
    (h : IsGlobalSigmaThreshold privateAt sigmaStar) :
    0 < sigmaStar :=
  h.1

theorem private_at
    {privateAt : ℝ → Prop} {sigmaStar : ℝ}
    (h : IsGlobalSigmaThreshold privateAt sigmaStar) :
    privateAt sigmaStar :=
  h.2.1

theorem private_iff_le
    {privateAt : ℝ → Prop} {sigmaStar sigma : ℝ}
    (h : IsGlobalSigmaThreshold privateAt sigmaStar)
    (hsigma : 0 < sigma) :
    privateAt sigma ↔ sigmaStar ≤ sigma :=
  h.2.2 sigma hsigma

theorem least_of_private
    {privateAt : ℝ → Prop} {sigmaStar sigma : ℝ}
    (h : IsGlobalSigmaThreshold privateAt sigmaStar)
    (hsigma : 0 < sigma)
    (hprivate : privateAt sigma) :
    sigmaStar ≤ sigma :=
  (h.private_iff_le hsigma).mp hprivate

theorem not_private_of_lt
    {privateAt : ℝ → Prop} {sigmaStar sigma : ℝ}
    (h : IsGlobalSigmaThreshold privateAt sigmaStar)
    (hsigma : 0 < sigma)
    (hlt : sigma < sigmaStar) :
    ¬ privateAt sigma := by
  intro hprivate
  exact (not_le_of_gt hlt) (h.least_of_private hsigma hprivate)

theorem unique
    {privateAt : ℝ → Prop} {left right : ℝ}
    (hleft : IsGlobalSigmaThreshold privateAt left)
    (hright : IsGlobalSigmaThreshold privateAt right) :
    left = right := by
  apply le_antisymm
  · exact hleft.least_of_private hright.positive hright.private_at
  · exact hright.least_of_private hleft.positive hleft.private_at

end IsGlobalSigmaThreshold

end

end Training
end DP
end Mf
