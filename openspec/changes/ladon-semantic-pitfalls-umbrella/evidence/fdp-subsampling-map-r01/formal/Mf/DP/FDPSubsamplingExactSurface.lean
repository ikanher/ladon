import Mf.DP.FDPSubsampling

namespace Mf
namespace DP

noncomputable section

/-!
Exact transport helpers beneath the public `f`-DP subsampling surface.

Current boundary:
- [FDPSubsampling.lean] exposes `PrivacyObject.subsampleTradeoffAt` only as the
  public tradeoff-side `C_p` operator.
- It does not yet realize a new subsampled neighboring law pair, `PLDPair`, or
  privacy object.

So the strongest exact generic layer currently available is transport *from the
input exact object* through `subsampleTradeoffAt`. This file packages that
boundary explicitly and gives theorem-facing helpers that downstream exact
accountant modules can reuse.

The next missing seam is stricter: Lean still needs an exact subsampled
neighboring object beneath `subsampleTradeoffAt` itself.
-/

namespace PrivacyObject

/-- Exact equality of privacy objects transports to equality of subsampled tradeoff surfaces. -/
@[simp] theorem subsampleTradeoffAt_eq_of_eq
    {U L : PrivacyObject}
    (h : U = L)
    (p ε : ℝ) :
    U.subsampleTradeoffAt p ε = L.subsampleTradeoffAt p ε := by
  cases h
  rfl

/-- Exact equality of privacy objects transports to pointwise comparison after subsampling. -/
theorem subsampleTradeoffAt_pointwiseLE_of_eq
    {U L : PrivacyObject}
    (h : U = L)
    (p ε : ℝ) :
    (U.subsampleTradeoffAt p ε).PointwiseLE (L.subsampleTradeoffAt p ε) := by
  simpa [subsampleTradeoffAt_eq_of_eq h p ε]

end PrivacyObject

namespace PLDPair

/--
Exact equality of neighboring `PLDPair`s transports through
`PrivacyObject.subsampleTradeoffAt`.
-/
theorem toSubsampleTradeoffAt_pointwiseLE_of_eq
    {U L : PLDPair}
    (h : U = L)
    {p : ℝ}
    (hp : 0 ≤ p)
    (ε : ℝ) :
    ((PrivacyObject.ofPLDPair U).subsampleTradeoffAt p ε).PointwiseLE
      ((PrivacyObject.ofPLDPair L).subsampleTradeoffAt p ε) := by
  exact PrivacyObject.subsampleTradeoffAt_of_leShiftedAdd_zero_zero
    (PLDPair.toPrivacyObject_leShiftedAdd_zero_zero_of_eq h) hp ε

end PLDPair

end
end DP
end Mf
