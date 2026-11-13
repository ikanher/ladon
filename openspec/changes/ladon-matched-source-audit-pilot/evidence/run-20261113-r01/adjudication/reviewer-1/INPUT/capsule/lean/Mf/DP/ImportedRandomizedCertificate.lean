import Mathlib.MeasureTheory.Measure.ProbabilityMeasure

namespace Mf
namespace DP

open scoped BigOperators

noncomputable section

/-!
# Generic imported randomized certificate facade

This module owns the route-agnostic certificate bookkeeping used by runtime
accountants.  It deliberately knows nothing about fixed-bin BNB, `b`-min-sep,
Gaussian mixtures, dynamic programs, or importance-sampling proposal laws.

The intended use is:

* a route-specific module supplies a real-valued privacy target;
* a runtime/theorem seam imports evidence that a reported upper bounds that
  target;
* this module proves the fixed-row, selected-row, selected-grid, and finite
  alpha-ledger consequences.

Sampler-law correctness, dynamic-program likelihood-ratio correctness,
KL-UCB/numeric inversion, and floating-point Gaussian/logsumexp correctness are
outside this module.
-/

/--
Abstract randomized upper-confidence bound over one target scalar.

`upperValue` is a random upper-bound function of the evidence outcome.  This
structure deliberately does not say how the upper was computed; KL-UCB,
empirical Bernstein, sampler exactness, and numeric evaluation are separate
theorem/import layers.
-/
structure RandomizedUpperConfidenceBoundAt
    {Ω : Type} [MeasurableSpace Ω]
    (sampleLaw : MeasureTheory.Measure Ω) [MeasureTheory.IsProbabilityMeasure sampleLaw]
    (target α : ℝ) where
  upperValue : Ω → ℝ
  highConfidence :
    sampleLaw.real {ω | target ≤ upperValue ω} ≥ 1 - α

namespace RandomizedUpperConfidenceBoundAt

/--
If an upper-confidence event is valid with probability at least `1 - α`, then
the event "passing the target cutoff implies target soundness" is valid with
the same probability.
-/
theorem measure_pass_implies_sound_ge
    {Ω : Type} [MeasurableSpace Ω]
    {sampleLaw : MeasureTheory.Measure Ω} [MeasureTheory.IsProbabilityMeasure sampleLaw]
    {target α : ℝ}
    (cert : RandomizedUpperConfidenceBoundAt sampleLaw target α)
    (δTarget : ℝ) :
    sampleLaw.real {ω | cert.upperValue ω ≤ δTarget → target ≤ δTarget}
      ≥ 1 - α := by
  let A : Set Ω := {ω | target ≤ cert.upperValue ω}
  let B : Set Ω := {ω | cert.upperValue ω ≤ δTarget → target ≤ δTarget}
  have hsubset : A ⊆ B := by
    intro ω hω hpass
    exact le_trans hω hpass
  have hmono : sampleLaw.real A ≤ sampleLaw.real B := by
    exact ENNReal.toReal_mono (by finiteness)
      (MeasureTheory.measure_mono hsubset)
  exact le_trans cert.highConfidence hmono

end RandomizedUpperConfidenceBoundAt

/--
Abstract randomized upper-confidence bound for a target selected from an
indexed candidate family.

This is the theorem-facing shape needed once runtime searches over gamma/sigma
candidates.  The field `highConfidence` is intentionally about the selected
target; it can be discharged from per-candidate KL-UCB bounds plus an explicit
alpha-spending/union-bound argument.
-/
structure RandomizedSelectedUpperConfidenceBoundAt
    {Ω ι : Type} [MeasurableSpace Ω]
    (sampleLaw : MeasureTheory.Measure Ω) [MeasureTheory.IsProbabilityMeasure sampleLaw]
    (target : ι → ℝ) (α : ℝ) where
  selected : Ω → ι
  upperValue : Ω → ℝ
  highConfidence :
    sampleLaw.real {ω | target (selected ω) ≤ upperValue ω} ≥ 1 - α

namespace RandomizedSelectedUpperConfidenceBoundAt

/--
High-confidence pass-implies-sound theorem for a selected target.

This is the selected-candidate analogue of
`RandomizedUpperConfidenceBoundAt.measure_pass_implies_sound_ge`.
-/
theorem measure_pass_implies_sound_ge
    {Ω ι : Type} [MeasurableSpace Ω]
    {sampleLaw : MeasureTheory.Measure Ω} [MeasureTheory.IsProbabilityMeasure sampleLaw]
    {target : ι → ℝ} {α : ℝ}
    (cert : RandomizedSelectedUpperConfidenceBoundAt sampleLaw target α)
    (δTarget : ℝ) :
    sampleLaw.real
        {ω | cert.upperValue ω ≤ δTarget → target (cert.selected ω) ≤ δTarget}
      ≥ 1 - α := by
  let A : Set Ω := {ω | target (cert.selected ω) ≤ cert.upperValue ω}
  let B : Set Ω :=
    {ω | cert.upperValue ω ≤ δTarget → target (cert.selected ω) ≤ δTarget}
  have hsubset : A ⊆ B := by
    intro ω hω hpass
    exact le_trans hω hpass
  have hmono : sampleLaw.real A ≤ sampleLaw.real B := by
    exact ENNReal.toReal_mono (by finiteness)
      (MeasureTheory.measure_mono hsubset)
  exact le_trans cert.highConfidence hmono

end RandomizedSelectedUpperConfidenceBoundAt

/--
Deterministic imported row certificate over one abstract target scalar.

This is the smallest Lean-facing facade for runtime artifacts after stochastic
verification has already produced/imported a row upper.  Route metadata is
recorded for auditability but does not drive the proof.
-/
structure ImportedCertificateRowAt (target δTarget : ℝ) where
  routeKind : String
  routeTarget : String
  certificateKind : String
  upper : ℝ
  upper_valid : target ≤ upper
  upper_le_target : upper ≤ δTarget

namespace ImportedCertificateRowAt

/-- A valid imported upper below the target cutoff certifies the target. -/
theorem sound
    {target δTarget : ℝ}
    (row : ImportedCertificateRowAt target δTarget) :
    target ≤ δTarget :=
  le_trans row.upper_valid row.upper_le_target

end ImportedCertificateRowAt

/--
Deterministic selected-grid certificate over a finite candidate bank.

This is the theorem-facing contract for runtime policies such as adaptive
racing.  The policy may decide which candidates receive verifier looks, but the
final artifact must expose a finite bank, a selected certified candidate, the
utility used for selection, and an imported upper-bound fact for every
certified candidate.
-/
structure FiniteSelectedGridCertificate
    (ι : Type) (target : ι → ℝ) (δTarget : ℝ) where
  candidateSet : Finset ι
  selected : ι
  selected_mem : selected ∈ candidateSet
  certified : ι → Prop
  selected_certified : certified selected
  utility : ι → ℝ
  upper : ι → ℝ
  certified_upper_valid :
    ∀ i, i ∈ candidateSet → certified i → target i ≤ upper i
  certified_upper_le_target :
    ∀ i, i ∈ candidateSet → certified i → upper i ≤ δTarget
  selected_min_utility :
    ∀ i, i ∈ candidateSet → certified i → utility selected ≤ utility i

namespace FiniteSelectedGridCertificate

/--
The selected certified candidate is sound whenever all certified candidates
carry valid uppers below the target cutoff.
-/
theorem sound
    {ι : Type} {target : ι → ℝ} {δTarget : ℝ}
    (cert : FiniteSelectedGridCertificate ι target δTarget) :
    target cert.selected ≤ δTarget :=
  le_trans
    (cert.certified_upper_valid cert.selected cert.selected_mem
      cert.selected_certified)
    (cert.certified_upper_le_target cert.selected cert.selected_mem
      cert.selected_certified)

/--
The selected candidate has utility no larger than any certified candidate in
the finite bank.  This is utility-selection evidence, not a privacy statement.
-/
theorem selected_utility_le_of_certified
    {ι : Type} {target : ι → ℝ} {δTarget : ℝ}
    (cert : FiniteSelectedGridCertificate ι target δTarget)
    {i : ι} (hi : i ∈ cert.candidateSet) (hcert : cert.certified i) :
    cert.utility cert.selected ≤ cert.utility i :=
  cert.selected_min_utility i hi hcert

end FiniteSelectedGridCertificate

/--
Finite union-bound seam for selected-grid accounting protocols.

The runtime may index bad events by any finite type of rows, looks, and
directions.  This theorem is deliberately generic: instantiate `ι` with the
finite finalist/look/direction index used by an artifact, and provide one bad
event per index.
-/
theorem finiteCandidateLookBadEventUnionBound
    {Ω ι : Type} [MeasurableSpace Ω]
    (sampleLaw : MeasureTheory.Measure Ω)
    (index : Finset ι)
    (badEvent : ι → Set Ω)
    (α : ι → ℝ)
    (hbad : ∀ i ∈ index, sampleLaw.real (badEvent i) ≤ α i) :
    sampleLaw.real (⋃ i ∈ index, badEvent i) ≤ ∑ i ∈ index, α i := by
  calc
    sampleLaw.real (⋃ i ∈ index, badEvent i)
        ≤ ∑ i ∈ index, sampleLaw.real (badEvent i) := by
          exact MeasureTheory.measureReal_biUnion_finset_le
            (μ := sampleLaw) index badEvent
    _ ≤ ∑ i ∈ index, α i := by
          exact Finset.sum_le_sum fun i hi => hbad i hi

/--
Finite alpha-ledger corollary for runtime artifacts.

This is the exact shape used by adaptive racing reports: if every evaluated
candidate/look/direction bad event consumes at most its row alpha, and the sum
of actually evaluated row alphas is below the declared global alpha, then the
probability of any false certified event is below the declared global alpha.
-/
theorem finiteCandidateLookBadEventUnionBound_le_total
    {Ω ι : Type} [MeasurableSpace Ω]
    (sampleLaw : MeasureTheory.Measure Ω)
    (index : Finset ι)
    (badEvent : ι → Set Ω)
    (α : ι → ℝ)
    (αTotal : ℝ)
    (hbad : ∀ i ∈ index, sampleLaw.real (badEvent i) ≤ α i)
    (hledger : (∑ i ∈ index, α i) ≤ αTotal) :
    sampleLaw.real (⋃ i ∈ index, badEvent i) ≤ αTotal :=
  le_trans
    (finiteCandidateLookBadEventUnionBound sampleLaw index badEvent α hbad)
    hledger

end
end DP
end Mf
