import Mf.DP.MMCCPoissonAmplificationComposition
import Mf.DP.ProfileConditionalComposition
import Mf.DP.ProductGaussianMixtureProfileDomination
import Mf.DP.GDPCompositionSurface

namespace Mf
namespace DP

noncomputable section

/-!
# PLD composition to ApproxDP bridge

This module isolates the generic bridge from an exact neighboring `PLDPair`
accountant object to event-level `ApproxDP` for the realized mechanism.

The current theorem surface is intentionally package-based:
- `ConcreteProfileApproxDPPackage` records a shared-base density realization of
  a mechanism family together with a concrete-profile bound,
- `CompFamilyProfileApproxDPPackage` adds the exact heterogeneous
  `PLDPair.compFamily` realization hook,
- the exported theorems turn those profile bounds into `ApproxDP`.

This keeps the generic bridge reusable while allowing downstream consumers to
supply their own exact product-law realization theorems.
-/

private theorem map_densityMeasure_measurableEquiv
    {α β : Type} [MeasurableSpace α] [MeasurableSpace β]
    (e : α ≃ᵐ β)
    (μ : MeasureTheory.Measure α) (f : β → ℝ) :
    MeasureTheory.Measure.map e (densityMeasure μ (f ∘ e))
      =
    densityMeasure (MeasureTheory.Measure.map e μ) f := by
  ext s hs
  rw [densityMeasure, densityMeasure, MeasurableEquiv.map_apply,
    MeasureTheory.withDensity_apply _ (e.measurable hs),
    MeasureTheory.withDensity_apply _ hs]
  calc
    ∫⁻ a in e ⁻¹' s, ENNReal.ofReal (f (e a)) ∂μ
      =
    ∫⁻ a,
      Set.indicator (e ⁻¹' s)
        (fun a => ENNReal.ofReal (f (e a))) a ∂μ := by
          rw [MeasureTheory.lintegral_indicator (e.measurable hs)]
    _ =
    ∫⁻ a, Set.indicator s (fun b => ENNReal.ofReal (f b)) (e a) ∂μ := by
      refine MeasureTheory.lintegral_congr_ae ?_
      filter_upwards with a
      by_cases ha : e a ∈ s <;> simp [ha]
    _ =
    ∫⁻ b, Set.indicator s (fun b => ENNReal.ofReal (f b)) b ∂MeasureTheory.Measure.map e μ := by
      simpa using
        (MeasureTheory.lintegral_map_equiv
          (μ := μ) (g := e)
          (f := Set.indicator s (fun b => ENNReal.ofReal (f b)))).symm
    _ =
    ∫⁻ b in s, ENNReal.ofReal (f b) ∂MeasureTheory.Measure.map e μ := by
      rw [MeasureTheory.lintegral_indicator hs]

/--
Push the prefix-product family together with the last coordinate back to the
full `Fin (n + 1)` product space.
-/
private def finSnocMap (n : ℕ) : (Fin n → ℝ) × ℝ → Fin (n + 1) → ℝ :=
  fun z => @Fin.snoc n (fun _ => ℝ) z.1 z.2

private theorem map_finSnoc_prod_pi_eq_pi
    (ν : Fin (n + 1) → MeasureTheory.Measure ℝ)
    [∀ i : Fin (n + 1), MeasureTheory.SigmaFinite (ν i)] :
    MeasureTheory.Measure.map (finSnocMap n)
      ((MeasureTheory.Measure.pi (fun i : Fin n => ν i.castSucc)).prod (ν (Fin.last n)))
      =
    MeasureTheory.Measure.pi ν := by
  let e := MeasurableEquiv.piFinSuccAbove (fun _ : Fin (n + 1) => ℝ) (Fin.last n)
  have hfun :
      finSnocMap n
        =
      (e.symm ∘ Prod.swap) := by
    funext z
    simp [finSnocMap, e, MeasurableEquiv.piFinSuccAbove_symm_apply, Fin.insertNthEquiv]
  calc
    MeasureTheory.Measure.map (finSnocMap n)
        ((MeasureTheory.Measure.pi (fun i : Fin n => ν i.castSucc)).prod (ν (Fin.last n)))
      =
    MeasureTheory.Measure.map (e.symm ∘ Prod.swap)
      ((MeasureTheory.Measure.pi (fun i : Fin n => ν i.castSucc)).prod (ν (Fin.last n))) := by
        simp [hfun]
    _ =
    MeasureTheory.Measure.map e.symm
      (MeasureTheory.Measure.map Prod.swap
        ((MeasureTheory.Measure.pi (fun i : Fin n => ν i.castSucc)).prod (ν (Fin.last n)))) := by
          rw [← MeasureTheory.Measure.map_map e.symm.measurable measurable_swap]
    _ =
    MeasureTheory.Measure.map e.symm
      ((ν (Fin.last n)).prod (MeasureTheory.Measure.pi (fun i : Fin n => ν i.castSucc))) := by
        rw [MeasureTheory.Measure.prod_swap]
    _ = MeasureTheory.Measure.pi ν := by
      simpa [e] using
        ((MeasureTheory.measurePreserving_piFinSuccAbove
          (μ := ν) (i := Fin.last n)).symm.map_eq)

/--
Shared-base product-density realization for an arbitrary finite measurable
family. This is the base-measure theorem underlying heterogeneous concrete
product `PLDPair` constructions.
-/
theorem densityMeasure_pi_family_eq_pi_densityMeasure_fin
    {β : Type} [MeasurableSpace β]
    (ν : MeasureTheory.Measure β) [MeasureTheory.SigmaFinite ν]
    (f : (i : Fin n) → β → ℝ)
    (hf_meas : ∀ i, Measurable (f i))
    (hf_nonneg : ∀ i x, 0 ≤ f i x) :
    densityMeasure
        (MeasureTheory.Measure.pi (fun _ : Fin n => ν))
        (fun z : Fin n → β => ∏ i : Fin n, f i (z i))
      =
    MeasureTheory.Measure.pi (fun i : Fin n => densityMeasure ν (f i)) := by
  induction n with
  | zero =>
      let e := MeasurableEquiv.ofUniqueOfUnique (Fin 0 → β) Unit
      apply (e.measurableEmbedding.map_injective)
      calc
        MeasureTheory.Measure.map e
            (densityMeasure
              (MeasureTheory.Measure.pi (fun _ : Fin 0 => ν))
              (fun z : Fin 0 → β => ∏ i : Fin 0, f i (z i)))
          =
        MeasureTheory.Measure.map e
          (MeasureTheory.Measure.pi (fun _ : Fin 0 => ν)) := by
            simp [densityMeasure]
        _ = MeasureTheory.Measure.dirac () := by
          simpa [e] using
            (MeasureTheory.measurePreserving_pi_empty (μ := fun _ : Fin 0 => ν)).map_eq
        _ =
        MeasureTheory.Measure.map e
          (MeasureTheory.Measure.pi (fun i : Fin 0 => densityMeasure ν (f i))) := by
            symm
            simpa [e] using
              (MeasureTheory.measurePreserving_pi_empty
                (μ := fun i : Fin 0 => densityMeasure ν (f i))).map_eq
  | succ n ih =>
      let e := MeasurableEquiv.piFinSuccAbove (fun _ : Fin (n + 1) => β) (Fin.last n)
      let g : β × (Fin n → β) → ℝ :=
        fun z => f (Fin.last n) z.1 * ∏ i : Fin n, f i.castSucc (z.2 i)
      have hcomp :
          g ∘ e = fun x : Fin (n + 1) → β => ∏ i : Fin (n + 1), f i (x i) := by
        funext x
        have hlast : (e x).1 = x (Fin.last n) := by
          simp [e]
        have htail : ∀ i : Fin n, (e x).2 i = x i.castSucc := by
          intro i
          have hinit : Fin.init x i = x i.castSucc := by
            simpa using congrFun (Fin.snoc_init_self x) i.castSucc
          simpa [e] using hinit
        calc
          g (e x) = f (Fin.last n) ((e x).1) * ∏ i : Fin n, f i.castSucc ((e x).2 i) := by
            simp [g]
          _ = f (Fin.last n) (x (Fin.last n)) * ∏ i : Fin n, f i.castSucc (x i.castSucc) := by
            rw [hlast]
            congr
            funext i
            simpa [htail i]
          _ = ∏ i : Fin (n + 1), f i (x i) := by
            rw [← Fin.snoc_init_self x]
            rw [Fin.prod_univ_castSucc]
            simp [Fin.snoc_castSucc, Fin.snoc_last, mul_comm]
      apply (e.measurableEmbedding.map_injective)
      calc
        MeasureTheory.Measure.map e
            (densityMeasure
              (MeasureTheory.Measure.pi (fun _ : Fin (n + 1) => ν))
              (fun z : Fin (n + 1) → β => ∏ i : Fin (n + 1), f i (z i)))
          =
        densityMeasure
          (MeasureTheory.Measure.map e
            (MeasureTheory.Measure.pi (fun _ : Fin (n + 1) => ν)))
          g := by
            simpa [hcomp] using
              (map_densityMeasure_measurableEquiv
                e
                (MeasureTheory.Measure.pi (fun _ : Fin (n + 1) => ν))
                g)
        _ =
        densityMeasure
          (ν.prod (MeasureTheory.Measure.pi (fun i : Fin n => ν)))
          g := by
            rw [show MeasureTheory.Measure.map e
                (MeasureTheory.Measure.pi (fun _ : Fin (n + 1) => ν))
                  =
                (ν.prod (MeasureTheory.Measure.pi (fun i : Fin n => ν))) by
                  simpa [e] using
                    (MeasureTheory.measurePreserving_piFinSuccAbove
                      (μ := fun _ : Fin (n + 1) => ν) (i := Fin.last n)).map_eq]
        _ =
        (densityMeasure ν (f (Fin.last n))).prod
          (densityMeasure
            (MeasureTheory.Measure.pi (fun i : Fin n => ν))
            (fun z : Fin n → β => ∏ i : Fin n, f i.castSucc (z i))) := by
            unfold densityMeasure g
            have hmul :
                (fun z : β × (Fin n → β) =>
                  ENNReal.ofReal (f (Fin.last n) z.1 * ∏ i : Fin n, f i.castSucc (z.2 i)))
                  =
                (fun z : β × (Fin n → β) =>
                  ENNReal.ofReal (f (Fin.last n) z.1)
                    * ENNReal.ofReal (∏ i : Fin n, f i.castSucc (z.2 i))) := by
                      funext z
                      rw [ENNReal.ofReal_mul]
                      exact hf_nonneg (Fin.last n) z.1
            have hmeas_prod :
                Measurable (fun z : Fin n → β => ∏ i : Fin n, f i.castSucc (z i)) := by
              fun_prop
            rw [hmul]
            rw [MeasureTheory.prod_withDensity
              (μ := ν)
              (ν := MeasureTheory.Measure.pi (fun _ : Fin n => ν))
              (f := fun a => ENNReal.ofReal (f (Fin.last n) a))
              (g := fun z : Fin n → β => ENNReal.ofReal (∏ i : Fin n, f i.castSucc (z i)))
              (by simpa using (hf_meas (Fin.last n)).ennreal_ofReal)
              (by simpa using hmeas_prod.ennreal_ofReal)]
        _ =
        (densityMeasure ν (f (Fin.last n))).prod
          (MeasureTheory.Measure.pi (fun i : Fin n => densityMeasure ν (f i.castSucc))) := by
            rw [ih (fun i => f i.castSucc) (fun i => hf_meas i.castSucc) (fun i x => hf_nonneg i.castSucc x)]
        _ =
        MeasureTheory.Measure.map e
          (MeasureTheory.Measure.pi (fun i : Fin (n + 1) => densityMeasure ν (f i))) := by
            haveI : ∀ i : Fin (n + 1), MeasureTheory.SigmaFinite (densityMeasure ν (f i)) := by
              intro i
              unfold densityMeasure
              infer_instance
            symm
            simpa [e] using
              (MeasureTheory.measurePreserving_piFinSuccAbove
                (μ := fun i : Fin (n + 1) => densityMeasure ν (f i)) (i := Fin.last n)).map_eq

/--
The coordinate privacy-loss map on a finite shared-base product is measurable
as soon as each coordinate density pair is measurable.
-/
theorem measurable_pi_forwardLossValue
    {α : Type} [MeasurableSpace α]
    {n : ℕ} {p q : Fin n → α → ℝ}
    (hp : ∀ i, Measurable (p i))
    (hq : ∀ i, Measurable (q i)) :
    Measurable (fun x : Fin n → α => fun i : Fin n => forwardLossValue (p i) (q i) (x i)) := by
  exact measurable_pi_lambda _
    (fun i => (measurable_forwardLossValue (hp i) (hq i)).comp (measurable_pi_apply i))

/--
Push a finite shared-base product source law through the coordinate forward-loss
map into the product of the mapped coordinate laws.

This is the product-measure step below the heterogeneous concrete-product
`PLDPair = compFamily` theorem. Sigma-finiteness of the mapped coordinate laws
is left explicit here and is handled by the downstream sigma-finiteness packet.
-/
theorem map_pi_densityMeasure_forwardLossValue_eq_pi_map
    {α : Type} [MeasurableSpace α]
    {n : ℕ}
    (μ : MeasureTheory.Measure α)
    (p q : Fin n → α → ℝ)
    (hp : ∀ i, Measurable (p i))
    (hq : ∀ i, Measurable (q i))
    (hσmap :
      ∀ i : Fin n,
        MeasureTheory.SigmaFinite
          ((densityMeasure μ (p i)).map (forwardLossValue (p i) (q i)))) :
    MeasureTheory.Measure.map
        (fun x : Fin n → α => fun i : Fin n => forwardLossValue (p i) (q i) (x i))
        (MeasureTheory.Measure.pi (fun i : Fin n => densityMeasure μ (p i)))
      =
    MeasureTheory.Measure.pi
      (fun i : Fin n => MeasureTheory.Measure.map (forwardLossValue (p i) (q i))
        (densityMeasure μ (p i))) := by
  let ν : Fin n → MeasureTheory.Measure α := fun i => densityMeasure μ (p i)
  let g : ∀ i : Fin n, α → ℝ := fun i => forwardLossValue (p i) (q i)
  have hg : ∀ i, AEMeasurable (g i) (ν i) := by
    intro i
    simpa [ν, g] using (measurable_forwardLossValue (hp i) (hq i)).aemeasurable
  letI : ∀ i : Fin n, MeasureTheory.SigmaFinite ((ν i).map (g i)) := by
    intro i
    simpa [ν, g] using hσmap i
  simpa [ν, g] using
    (MeasureTheory.Measure.pi_map_pi (μ := ν) (f := g) (hf := hg))

/--
If the source density measure is finite, then its forward mapped privacy-loss
law is automatically sigma-finite.
-/
theorem sigmaFinite_map_forwardLossValue_of_isFiniteDensityMeasure
    {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α)
    (p q : α → ℝ)
    [MeasureTheory.IsFiniteMeasure (densityMeasure μ p)] :
    MeasureTheory.SigmaFinite
      ((densityMeasure μ p).map (forwardLossValue p q)) := by
  infer_instance

/--
If the reverse source density measure is finite, then its mapped privacy-loss
law is automatically sigma-finite.
-/
theorem sigmaFinite_map_reverseForwardLossValue_of_isFiniteDensityMeasure
    {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α)
    (p q : α → ℝ)
    [MeasureTheory.IsFiniteMeasure (densityMeasure μ q)] :
    MeasureTheory.SigmaFinite
      ((densityMeasure μ q).map (forwardLossValue q p)) := by
  infer_instance

/--
Transport forward mapped-law sigma-finiteness from a known finite source
realization of `densityMeasure μ p`.
-/
theorem sigmaFinite_map_forwardLossValue_of_eq_densityMeasure
    {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α)
    (p q : α → ℝ)
    (ν : MeasureTheory.Measure α)
    [MeasureTheory.IsFiniteMeasure ν]
    (hν : ν = densityMeasure μ p) :
    MeasureTheory.SigmaFinite
      ((densityMeasure μ p).map (forwardLossValue p q)) := by
  rw [← hν]
  infer_instance

/--
Transport reverse mapped-law sigma-finiteness from a known finite source
realization of `densityMeasure μ q`.
-/
theorem sigmaFinite_map_reverseForwardLossValue_of_eq_densityMeasure
    {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α)
    (p q : α → ℝ)
    (ν : MeasureTheory.Measure α)
    [MeasureTheory.IsFiniteMeasure ν]
    (hν : ν = densityMeasure μ q) :
    MeasureTheory.SigmaFinite
      ((densityMeasure μ q).map (forwardLossValue q p)) := by
  rw [← hν]
  infer_instance

/--
Package the forward mapped-law sigma-finiteness obligations for a finite shared
base family from explicit finite source-law realizations at each coordinate.

This is the theorem-facing transport layer used by the blocked heterogeneous
concrete-product `PLDPair = compFamily` proof.
-/
theorem sigmaFinite_map_forwardLossValue_family_of_eq_densityMeasure
    {α : Type} [MeasurableSpace α]
    {n : ℕ}
    (μ : MeasureTheory.Measure α)
    (p q : Fin n → α → ℝ)
    (ν : Fin n → MeasureTheory.Measure α)
    [∀ i : Fin n, MeasureTheory.IsFiniteMeasure (ν i)]
    (hν : ∀ i : Fin n, ν i = densityMeasure μ (p i)) :
    ∀ i : Fin n,
      MeasureTheory.SigmaFinite
        ((densityMeasure μ (p i)).map (forwardLossValue (p i) (q i))) := by
  intro i
  exact sigmaFinite_map_forwardLossValue_of_eq_densityMeasure
    (μ := μ) (p := p i) (q := q i) (ν := ν i) (hν := hν i)

/--
Package the reverse mapped-law sigma-finiteness obligations for a finite shared
base family from explicit finite source-law realizations at each coordinate.

This is the reverse-law companion to
`sigmaFinite_map_forwardLossValue_family_of_eq_densityMeasure`.
-/
theorem sigmaFinite_map_reverseForwardLossValue_family_of_eq_densityMeasure
    {α : Type} [MeasurableSpace α]
    {n : ℕ}
    (μ : MeasureTheory.Measure α)
    (p q : Fin n → α → ℝ)
    (ν : Fin n → MeasureTheory.Measure α)
    [∀ i : Fin n, MeasureTheory.IsFiniteMeasure (ν i)]
    (hν : ∀ i : Fin n, ν i = densityMeasure μ (q i)) :
    ∀ i : Fin n,
      MeasureTheory.SigmaFinite
        ((densityMeasure μ (q i)).map (forwardLossValue (q i) (p i))) := by
  intro i
  exact sigmaFinite_map_reverseForwardLossValue_of_eq_densityMeasure
    (μ := μ) (p := p i) (q := q i) (ν := ν i) (hν := hν i)

namespace PLDPair

/--
The forward law of a heterogeneous exact composition is the pushforward of the
product of the coordinate forward laws by coordinate sum.
-/
@[simp] theorem compFamily_forward_eq_pi_map_sum
    {n : ℕ} (L : Fin n → PLDPair)
    [∀ i : Fin n, MeasureTheory.SigmaFinite (L i).forward] :
    (PLDPair.compFamily L).forward
      =
    MeasureTheory.Measure.map (fun x : Fin n → ℝ => ∑ i, x i)
      (MeasureTheory.Measure.pi (fun i : Fin n => (L i).forward)) := by
  induction n with
  | zero =>
      calc
        (PLDPair.compFamily L).forward = MeasureTheory.Measure.dirac 0 := by
          simp [PLDPair.compFamily, PLDPair.id]
        _ =
        MeasureTheory.Measure.map (fun _ : Fin 0 → ℝ => (0 : ℝ))
          (MeasureTheory.Measure.pi (fun i : Fin 0 => (L i).forward)) := by
            rw [MeasureTheory.Measure.map_const]
            simp
        _ =
        MeasureTheory.Measure.map (fun x : Fin 0 → ℝ => ∑ i, x i)
          (MeasureTheory.Measure.pi (fun i : Fin 0 => (L i).forward)) := by
            simp
  | succ n ih =>
      let Linit : Fin n → PLDPair := fun i => L (finPrefixInclusion n i)
      let sumN : (Fin n → ℝ) → ℝ := fun x => ∑ i, x i
      let sumSucc : (Fin (n + 1) → ℝ) → ℝ := fun x => ∑ i, x i
      have hsumN : Measurable sumN := by
        dsimp [sumN]
        fun_prop
      have hsumSucc : Measurable sumSucc := by
        dsimp [sumSucc]
        fun_prop
      have hcompose :
          ((fun w : ℝ × ℝ => w.1 + w.2) ∘ Prod.map sumN (fun x : ℝ => x))
            =
          sumSucc ∘ finSnocMap n := by
        funext z
        simp [sumN, sumSucc, finSnocMap, Fin.sum_univ_castSucc, add_comm]
      have hprod :
          ((MeasureTheory.Measure.map sumN
              (MeasureTheory.Measure.pi (fun i : Fin n => (Linit i).forward))).prod
              (L (Fin.last n)).forward)
            =
          MeasureTheory.Measure.map (Prod.map sumN (fun x : ℝ => x))
            ((MeasureTheory.Measure.pi (fun i : Fin n => (Linit i).forward)).prod
              (L (Fin.last n)).forward) := by
              calc
                ((MeasureTheory.Measure.map sumN
                    (MeasureTheory.Measure.pi (fun i : Fin n => (Linit i).forward))).prod
                    (L (Fin.last n)).forward)
                  =
                ((MeasureTheory.Measure.map sumN
                    (MeasureTheory.Measure.pi (fun i : Fin n => (Linit i).forward))).prod
                    (MeasureTheory.Measure.map (fun x : ℝ => x) ((L (Fin.last n)).forward))) := by
                      simp
                _ =
                MeasureTheory.Measure.map (Prod.map sumN (fun x : ℝ => x))
                  ((MeasureTheory.Measure.pi (fun i : Fin n => (Linit i).forward)).prod
                    (L (Fin.last n)).forward) := by
                      exact
                        (MeasureTheory.Measure.map_prod_map
                          (MeasureTheory.Measure.pi (fun i : Fin n => (Linit i).forward))
                          ((L (Fin.last n)).forward) hsumN measurable_id)
      calc
        (PLDPair.compFamily L).forward
          =
        MeasureTheory.Measure.map (fun w : ℝ × ℝ => w.1 + w.2)
          ((MeasureTheory.Measure.map sumN
              (MeasureTheory.Measure.pi (fun i : Fin n => (Linit i).forward))).prod
              (L (Fin.last n)).forward) := by
                rw [PLDPair.compFamily_succ, PLDPair.comp_forward, ih]
        _ =
        MeasureTheory.Measure.map (fun w : ℝ × ℝ => w.1 + w.2)
          (MeasureTheory.Measure.map (Prod.map sumN (fun x : ℝ => x))
            ((MeasureTheory.Measure.pi (fun i : Fin n => (Linit i).forward)).prod
              (L (Fin.last n)).forward)) := by
                exact congrArg (MeasureTheory.Measure.map (fun w : ℝ × ℝ => w.1 + w.2)) hprod
        _ =
        MeasureTheory.Measure.map
          (((fun w : ℝ × ℝ => w.1 + w.2) ∘ Prod.map sumN (fun x : ℝ => x)))
          ((MeasureTheory.Measure.pi (fun i : Fin n => (Linit i).forward)).prod
            (L (Fin.last n)).forward) := by
              rw [← MeasureTheory.Measure.map_map (by fun_prop) (by fun_prop)]
        _ =
        MeasureTheory.Measure.map (sumSucc ∘ finSnocMap n)
          ((MeasureTheory.Measure.pi (fun i : Fin n => (Linit i).forward)).prod
            (L (Fin.last n)).forward) := by
              rw [hcompose]
        _ =
        MeasureTheory.Measure.map sumSucc
          (MeasureTheory.Measure.map (finSnocMap n)
            ((MeasureTheory.Measure.pi (fun i : Fin n => (Linit i).forward)).prod
              (L (Fin.last n)).forward)) := by
                have hfinSnoc : Measurable (finSnocMap n) := by
                  exact
                    ((continuous_fst.finSnoc continuous_snd).measurable :
                      Measurable (fun z : (Fin n → ℝ) × ℝ =>
                        @Fin.snoc n (fun _ => ℝ) z.1 z.2))
                rw [← MeasureTheory.Measure.map_map hsumSucc hfinSnoc]
        _ =
        MeasureTheory.Measure.map sumSucc
          (MeasureTheory.Measure.pi (fun i : Fin (n + 1) => (L i).forward)) := by
            exact congrArg (MeasureTheory.Measure.map sumSucc)
              (by exact
                map_finSnoc_prod_pi_eq_pi (ν := fun i : Fin (n + 1) => (L i).forward))

/--
The reverse law of a heterogeneous exact composition is the pushforward of the
product of the coordinate reverse laws by coordinate sum.
-/
@[simp] theorem compFamily_reverse_eq_pi_map_sum
    {n : ℕ} (L : Fin n → PLDPair)
    [∀ i : Fin n, MeasureTheory.SigmaFinite (L i).reverse] :
    (PLDPair.compFamily L).reverse
      =
    MeasureTheory.Measure.map (fun x : Fin n → ℝ => ∑ i, x i)
      (MeasureTheory.Measure.pi (fun i : Fin n => (L i).reverse)) := by
  induction n with
  | zero =>
      calc
        (PLDPair.compFamily L).reverse = MeasureTheory.Measure.dirac 0 := by
          simp [PLDPair.compFamily, PLDPair.id]
        _ =
        MeasureTheory.Measure.map (fun _ : Fin 0 → ℝ => (0 : ℝ))
          (MeasureTheory.Measure.pi (fun i : Fin 0 => (L i).reverse)) := by
            rw [MeasureTheory.Measure.map_const]
            simp
        _ =
        MeasureTheory.Measure.map (fun x : Fin 0 → ℝ => ∑ i, x i)
          (MeasureTheory.Measure.pi (fun i : Fin 0 => (L i).reverse)) := by
            simp
  | succ n ih =>
      let Linit : Fin n → PLDPair := fun i => L (finPrefixInclusion n i)
      let sumN : (Fin n → ℝ) → ℝ := fun x => ∑ i, x i
      let sumSucc : (Fin (n + 1) → ℝ) → ℝ := fun x => ∑ i, x i
      have hsumN : Measurable sumN := by
        dsimp [sumN]
        fun_prop
      have hsumSucc : Measurable sumSucc := by
        dsimp [sumSucc]
        fun_prop
      have hcompose :
          ((fun w : ℝ × ℝ => w.1 + w.2) ∘ Prod.map sumN (fun x : ℝ => x))
            =
          sumSucc ∘ finSnocMap n := by
        funext z
        simp [sumN, sumSucc, finSnocMap, Fin.sum_univ_castSucc, add_comm]
      have hprod :
          ((MeasureTheory.Measure.map sumN
              (MeasureTheory.Measure.pi (fun i : Fin n => (Linit i).reverse))).prod
              (L (Fin.last n)).reverse)
            =
          MeasureTheory.Measure.map (Prod.map sumN (fun x : ℝ => x))
            ((MeasureTheory.Measure.pi (fun i : Fin n => (Linit i).reverse)).prod
              (L (Fin.last n)).reverse) := by
              calc
                ((MeasureTheory.Measure.map sumN
                    (MeasureTheory.Measure.pi (fun i : Fin n => (Linit i).reverse))).prod
                    (L (Fin.last n)).reverse)
                  =
                ((MeasureTheory.Measure.map sumN
                    (MeasureTheory.Measure.pi (fun i : Fin n => (Linit i).reverse))).prod
                    (MeasureTheory.Measure.map (fun x : ℝ => x) ((L (Fin.last n)).reverse))) := by
                      simp
                _ =
                MeasureTheory.Measure.map (Prod.map sumN (fun x : ℝ => x))
                  ((MeasureTheory.Measure.pi (fun i : Fin n => (Linit i).reverse)).prod
                    (L (Fin.last n)).reverse) := by
                      exact
                        (MeasureTheory.Measure.map_prod_map
                          (MeasureTheory.Measure.pi (fun i : Fin n => (Linit i).reverse))
                          ((L (Fin.last n)).reverse) hsumN measurable_id)
      calc
        (PLDPair.compFamily L).reverse
          =
        MeasureTheory.Measure.map (fun w : ℝ × ℝ => w.1 + w.2)
          ((MeasureTheory.Measure.map sumN
              (MeasureTheory.Measure.pi (fun i : Fin n => (Linit i).reverse))).prod
              (L (Fin.last n)).reverse) := by
                rw [PLDPair.compFamily_succ, PLDPair.comp_reverse, ih]
        _ =
        MeasureTheory.Measure.map (fun w : ℝ × ℝ => w.1 + w.2)
          (MeasureTheory.Measure.map (Prod.map sumN (fun x : ℝ => x))
            ((MeasureTheory.Measure.pi (fun i : Fin n => (Linit i).reverse)).prod
              (L (Fin.last n)).reverse)) := by
                exact congrArg (MeasureTheory.Measure.map (fun w : ℝ × ℝ => w.1 + w.2)) hprod
        _ =
        MeasureTheory.Measure.map
          (((fun w : ℝ × ℝ => w.1 + w.2) ∘ Prod.map sumN (fun x : ℝ => x)))
          ((MeasureTheory.Measure.pi (fun i : Fin n => (Linit i).reverse)).prod
            (L (Fin.last n)).reverse) := by
              rw [← MeasureTheory.Measure.map_map (by fun_prop) (by fun_prop)]
        _ =
        MeasureTheory.Measure.map (sumSucc ∘ finSnocMap n)
          ((MeasureTheory.Measure.pi (fun i : Fin n => (Linit i).reverse)).prod
            (L (Fin.last n)).reverse) := by
              rw [hcompose]
        _ =
        MeasureTheory.Measure.map sumSucc
          (MeasureTheory.Measure.map (finSnocMap n)
            ((MeasureTheory.Measure.pi (fun i : Fin n => (Linit i).reverse)).prod
              (L (Fin.last n)).reverse)) := by
                have hfinSnoc : Measurable (finSnocMap n) := by
                  exact
                    ((continuous_fst.finSnoc continuous_snd).measurable :
                      Measurable (fun z : (Fin n → ℝ) × ℝ =>
                        @Fin.snoc n (fun _ => ℝ) z.1 z.2))
                rw [← MeasureTheory.Measure.map_map hsumSucc hfinSnoc]
        _ =
        MeasureTheory.Measure.map sumSucc
          (MeasureTheory.Measure.pi (fun i : Fin (n + 1) => (L i).reverse)) := by
            exact congrArg (MeasureTheory.Measure.map sumSucc)
              (by exact
                map_finSnoc_prod_pi_eq_pi (ν := fun i : Fin (n + 1) => (L i).reverse))

/-- Pair-level `pi-map-sum` form of heterogeneous exact composition. -/
@[simp] theorem compFamily_eq_pi_map_sum
    {n : ℕ} (L : Fin n → PLDPair)
    [∀ i : Fin n, MeasureTheory.SigmaFinite (L i).forward]
    [∀ i : Fin n, MeasureTheory.SigmaFinite (L i).reverse] :
    PLDPair.compFamily L
      =
    { forward := MeasureTheory.Measure.map (fun x : Fin n → ℝ => ∑ i, x i)
          (MeasureTheory.Measure.pi (fun i : Fin n => (L i).forward))
      , reverse := MeasureTheory.Measure.map (fun x : Fin n → ℝ => ∑ i, x i)
          (MeasureTheory.Measure.pi (fun i : Fin n => (L i).reverse)) } := by
  cases h : PLDPair.compFamily L with
  | mk forward reverse =>
      have hf :
          forward =
            MeasureTheory.Measure.map (fun x : Fin n → ℝ => ∑ i, x i)
              (MeasureTheory.Measure.pi (fun i : Fin n => (L i).forward)) := by
                simpa [h] using
                  (PLDPair.compFamily_forward_eq_pi_map_sum (L := L))
      have hr :
          reverse =
            MeasureTheory.Measure.map (fun x : Fin n → ℝ => ∑ i, x i)
              (MeasureTheory.Measure.pi (fun i : Fin n => (L i).reverse)) := by
                simpa [h] using
                  (PLDPair.compFamily_reverse_eq_pi_map_sum (L := L))
      cases hL : PLDPair.compFamily L with
      | mk =>
          simp [hf, hr]

end PLDPair

/--
The concrete forward law of a finite heterogeneous shared-base product density
is exactly the forward law of the composed coordinate `PLDPair.compFamily`.
-/
theorem concretePLDPair_sharedBaseProduct_forward_eq_compFamily
    {α : Type} [MeasurableSpace α]
    {n : ℕ}
    (μ : MeasureTheory.Measure α) [MeasureTheory.SigmaFinite μ]
    (p q : Fin n → α → ℝ)
    (hp_meas : ∀ i, Measurable (p i))
    (hq_meas : ∀ i, Measurable (q i))
    (hp_nonneg : ∀ i x, 0 ≤ p i x)
    (hq_nonneg : ∀ i x, 0 ≤ q i x)
    (hp_pos : ∀ i x, 0 < p i x)
    (hq_pos : ∀ i x, 0 < q i x)
    [∀ i : Fin n, MeasureTheory.IsFiniteMeasure (densityMeasure μ (p i))]
    [∀ i : Fin n, MeasureTheory.IsFiniteMeasure (densityMeasure μ (q i))] :
    (concretePLDPair
      (MeasureTheory.Measure.pi (fun _ : Fin n => μ))
      (fun z : Fin n → α => ∏ i : Fin n, p i (z i))
      (fun z : Fin n → α => ∏ i : Fin n, q i (z i))).forward
      =
    (PLDPair.compFamily (fun i : Fin n => concretePLDPair μ (p i) (q i))).forward := by
  let prodp : (Fin n → α) → ℝ := fun z => ∏ i : Fin n, p i (z i)
  let prodq : (Fin n → α) → ℝ := fun z => ∏ i : Fin n, q i (z i)
  let coordLoss : (Fin n → α) → Fin n → ℝ :=
    fun z i => forwardLossValue (p i) (q i) (z i)
  have hcoord_meas : Measurable coordLoss := by
    simpa [coordLoss] using measurable_pi_forwardLossValue hp_meas hq_meas
  have hsum_meas : Measurable (fun z : Fin n → ℝ => ∑ i, z i) := by
    fun_prop
  have hloss :
      forwardLossValue prodp prodq = (fun z : Fin n → α => ∑ i : Fin n, coordLoss z i) := by
    funext z
    have hpprod_pos : 0 < ∏ i : Fin n, p i (z i) := by
      refine Finset.prod_pos ?_
      intro i hi
      exact hp_pos i (z i)
    have hqprod_pos : 0 < ∏ i : Fin n, q i (z i) := by
      refine Finset.prod_pos ?_
      intro i hi
      exact hq_pos i (z i)
    rw [forwardLossValue, Real.log_div hpprod_pos.ne' hqprod_pos.ne']
    rw [show Real.log (∏ i : Fin n, p i (z i)) = ∑ i : Fin n, Real.log (p i (z i)) by
      rw [Real.log_prod]
      intro i hi
      exact (hp_pos i (z i)).ne']
    rw [show Real.log (∏ i : Fin n, q i (z i)) = ∑ i : Fin n, Real.log (q i (z i)) by
      rw [Real.log_prod]
      intro i hi
      exact (hq_pos i (z i)).ne']
    rw [← Finset.sum_sub_distrib]
    refine Finset.sum_congr rfl ?_
    intro i hi
    simp [coordLoss, forwardLossValue, Real.log_div (hp_pos i (z i)).ne' (hq_pos i (z i)).ne']
  have hmap :
      MeasureTheory.Measure.map (forwardLossValue prodp prodq)
        (densityMeasure (MeasureTheory.Measure.pi (fun _ : Fin n => μ)) prodp)
        =
      MeasureTheory.Measure.map (fun z : Fin n → ℝ => ∑ i, z i)
        (MeasureTheory.Measure.map coordLoss
          (densityMeasure (MeasureTheory.Measure.pi (fun _ : Fin n => μ)) prodp)) := by
    calc
      MeasureTheory.Measure.map (forwardLossValue prodp prodq)
        (densityMeasure (MeasureTheory.Measure.pi (fun _ : Fin n => μ)) prodp)
        =
      MeasureTheory.Measure.map (fun z : Fin n → α => ∑ i : Fin n, coordLoss z i)
        (densityMeasure (MeasureTheory.Measure.pi (fun _ : Fin n => μ)) prodp) := by
          simp [hloss]
      _ =
      MeasureTheory.Measure.map
        (((fun z : Fin n → ℝ => ∑ i : Fin n, z i) : (Fin n → ℝ) → ℝ) ∘ coordLoss)
        (densityMeasure (MeasureTheory.Measure.pi (fun _ : Fin n => μ)) prodp) := by
          rfl
      _ =
      MeasureTheory.Measure.map (fun z : Fin n → ℝ => ∑ i, z i)
        (MeasureTheory.Measure.map coordLoss
          (densityMeasure (MeasureTheory.Measure.pi (fun _ : Fin n => μ)) prodp)) := by
          rw [← MeasureTheory.Measure.map_map hsum_meas hcoord_meas]
  have hpi :
      MeasureTheory.Measure.map coordLoss
        (densityMeasure (MeasureTheory.Measure.pi (fun _ : Fin n => μ)) prodp)
      =
      MeasureTheory.Measure.pi
        (fun i : Fin n => MeasureTheory.Measure.map (forwardLossValue (p i) (q i))
          (densityMeasure μ (p i))) := by
    rw [densityMeasure_pi_family_eq_pi_densityMeasure_fin
      (ν := μ) (f := p) hp_meas hp_nonneg]
    exact map_pi_densityMeasure_forwardLossValue_eq_pi_map
      μ p q hp_meas hq_meas
      (sigmaFinite_map_forwardLossValue_family_of_eq_densityMeasure
        (μ := μ) (p := p) (q := q)
        (ν := fun i : Fin n => densityMeasure μ (p i))
        (hν := fun i => rfl))
  letI : ∀ i : Fin n, MeasureTheory.SigmaFinite ((concretePLDPair μ (p i) (q i)).forward) := by
    intro i
    simpa [concretePLDPair, forwardLossLaw] using
      (sigmaFinite_map_forwardLossValue_family_of_eq_densityMeasure
        (μ := μ) (p := p) (q := q)
        (ν := fun i : Fin n => densityMeasure μ (p i))
        (hν := fun i => rfl) i)
  calc
    (concretePLDPair
      (MeasureTheory.Measure.pi (fun _ : Fin n => μ))
      (fun z : Fin n → α => ∏ i : Fin n, p i (z i))
      (fun z : Fin n → α => ∏ i : Fin n, q i (z i))).forward
      =
    MeasureTheory.Measure.map (forwardLossValue prodp prodq)
      (densityMeasure (MeasureTheory.Measure.pi (fun _ : Fin n => μ)) prodp) := by
        rfl
    _ =
    MeasureTheory.Measure.map (fun z : Fin n → ℝ => ∑ i, z i)
      (MeasureTheory.Measure.map coordLoss
        (densityMeasure (MeasureTheory.Measure.pi (fun _ : Fin n => μ)) prodp)) := hmap
    _ =
    MeasureTheory.Measure.map (fun z : Fin n → ℝ => ∑ i, z i)
      (MeasureTheory.Measure.pi
        (fun i : Fin n => MeasureTheory.Measure.map (forwardLossValue (p i) (q i))
          (densityMeasure μ (p i)))) := by
        rw [hpi]
    _ =
    (PLDPair.compFamily (fun i : Fin n => concretePLDPair μ (p i) (q i))).forward := by
      symm
      simpa [concretePLDPair, forwardLossLaw] using
        (PLDPair.compFamily_forward_eq_pi_map_sum
          (L := fun i : Fin n => concretePLDPair μ (p i) (q i)))

/--
The concrete reverse law of a finite heterogeneous shared-base product density
is exactly the reverse law of the composed coordinate `PLDPair.compFamily`.
-/
theorem concretePLDPair_sharedBaseProduct_reverse_eq_compFamily
    {α : Type} [MeasurableSpace α]
    {n : ℕ}
    (μ : MeasureTheory.Measure α) [MeasureTheory.SigmaFinite μ]
    (p q : Fin n → α → ℝ)
    (hp_meas : ∀ i, Measurable (p i))
    (hq_meas : ∀ i, Measurable (q i))
    (hp_nonneg : ∀ i x, 0 ≤ p i x)
    (hq_nonneg : ∀ i x, 0 ≤ q i x)
    (hp_pos : ∀ i x, 0 < p i x)
    (hq_pos : ∀ i x, 0 < q i x)
    [∀ i : Fin n, MeasureTheory.IsFiniteMeasure (densityMeasure μ (p i))]
    [∀ i : Fin n, MeasureTheory.IsFiniteMeasure (densityMeasure μ (q i))] :
    (concretePLDPair
      (MeasureTheory.Measure.pi (fun _ : Fin n => μ))
      (fun z : Fin n → α => ∏ i : Fin n, p i (z i))
      (fun z : Fin n → α => ∏ i : Fin n, q i (z i))).reverse
      =
    (PLDPair.compFamily (fun i : Fin n => concretePLDPair μ (p i) (q i))).reverse := by
  let prodp : (Fin n → α) → ℝ := fun z => ∏ i : Fin n, p i (z i)
  let prodq : (Fin n → α) → ℝ := fun z => ∏ i : Fin n, q i (z i)
  let coordLoss : (Fin n → α) → Fin n → ℝ :=
    fun z i => forwardLossValue (q i) (p i) (z i)
  have hcoord_meas : Measurable coordLoss := by
    exact measurable_pi_lambda _ (fun i =>
      (measurable_forwardLossValue (hq_meas i) (hp_meas i)).comp (measurable_pi_apply i))
  have hsum_meas : Measurable (fun z : Fin n → ℝ => ∑ i, z i) := by
    fun_prop
  have hloss :
      forwardLossValue prodq prodp = (fun z : Fin n → α => ∑ i : Fin n, coordLoss z i) := by
    funext z
    have hqprod_pos : 0 < ∏ i : Fin n, q i (z i) := by
      refine Finset.prod_pos ?_
      intro i hi
      exact hq_pos i (z i)
    have hpprod_pos : 0 < ∏ i : Fin n, p i (z i) := by
      refine Finset.prod_pos ?_
      intro i hi
      exact hp_pos i (z i)
    rw [forwardLossValue, Real.log_div hqprod_pos.ne' hpprod_pos.ne']
    rw [show Real.log (∏ i : Fin n, q i (z i)) = ∑ i : Fin n, Real.log (q i (z i)) by
      rw [Real.log_prod]
      intro i hi
      exact (hq_pos i (z i)).ne']
    rw [show Real.log (∏ i : Fin n, p i (z i)) = ∑ i : Fin n, Real.log (p i (z i)) by
      rw [Real.log_prod]
      intro i hi
      exact (hp_pos i (z i)).ne']
    rw [← Finset.sum_sub_distrib]
    refine Finset.sum_congr rfl ?_
    intro i hi
    simp [coordLoss, forwardLossValue, Real.log_div (hq_pos i (z i)).ne' (hp_pos i (z i)).ne']
  have hmap :
      MeasureTheory.Measure.map (forwardLossValue prodq prodp)
        (densityMeasure (MeasureTheory.Measure.pi (fun _ : Fin n => μ)) prodq)
        =
      MeasureTheory.Measure.map (fun z : Fin n → ℝ => ∑ i, z i)
        (MeasureTheory.Measure.map coordLoss
          (densityMeasure (MeasureTheory.Measure.pi (fun _ : Fin n => μ)) prodq)) := by
    calc
      MeasureTheory.Measure.map (forwardLossValue prodq prodp)
        (densityMeasure (MeasureTheory.Measure.pi (fun _ : Fin n => μ)) prodq)
        =
      MeasureTheory.Measure.map (fun z : Fin n → α => ∑ i : Fin n, coordLoss z i)
        (densityMeasure (MeasureTheory.Measure.pi (fun _ : Fin n => μ)) prodq) := by
          simp [hloss]
      _ =
      MeasureTheory.Measure.map
        (((fun z : Fin n → ℝ => ∑ i : Fin n, z i) : (Fin n → ℝ) → ℝ) ∘ coordLoss)
        (densityMeasure (MeasureTheory.Measure.pi (fun _ : Fin n => μ)) prodq) := by
          rfl
      _ =
      MeasureTheory.Measure.map (fun z : Fin n → ℝ => ∑ i, z i)
        (MeasureTheory.Measure.map coordLoss
          (densityMeasure (MeasureTheory.Measure.pi (fun _ : Fin n => μ)) prodq)) := by
          rw [← MeasureTheory.Measure.map_map hsum_meas hcoord_meas]
  have hpi :
      MeasureTheory.Measure.map coordLoss
        (densityMeasure (MeasureTheory.Measure.pi (fun _ : Fin n => μ)) prodq)
      =
      MeasureTheory.Measure.pi
        (fun i : Fin n => MeasureTheory.Measure.map (forwardLossValue (q i) (p i))
          (densityMeasure μ (q i))) := by
    rw [densityMeasure_pi_family_eq_pi_densityMeasure_fin
      (ν := μ) (f := q) hq_meas hq_nonneg]
    exact map_pi_densityMeasure_forwardLossValue_eq_pi_map
      μ q p hq_meas hp_meas
      (sigmaFinite_map_reverseForwardLossValue_family_of_eq_densityMeasure
        (μ := μ) (p := p) (q := q)
        (ν := fun i : Fin n => densityMeasure μ (q i))
        (hν := fun i => rfl))
  letI : ∀ i : Fin n, MeasureTheory.SigmaFinite ((concretePLDPair μ (p i) (q i)).reverse) := by
    intro i
    simpa [concretePLDPair, reverseLossLaw] using
      (sigmaFinite_map_reverseForwardLossValue_family_of_eq_densityMeasure
        (μ := μ) (p := p) (q := q)
        (ν := fun i : Fin n => densityMeasure μ (q i))
        (hν := fun i => rfl) i)
  calc
    (concretePLDPair
      (MeasureTheory.Measure.pi (fun _ : Fin n => μ))
      (fun z : Fin n → α => ∏ i : Fin n, p i (z i))
      (fun z : Fin n → α => ∏ i : Fin n, q i (z i))).reverse
      =
    MeasureTheory.Measure.map (forwardLossValue prodq prodp)
      (densityMeasure (MeasureTheory.Measure.pi (fun _ : Fin n => μ)) prodq) := by
        rfl
    _ =
    MeasureTheory.Measure.map (fun z : Fin n → ℝ => ∑ i, z i)
      (MeasureTheory.Measure.map coordLoss
        (densityMeasure (MeasureTheory.Measure.pi (fun _ : Fin n => μ)) prodq)) := hmap
    _ =
    MeasureTheory.Measure.map (fun z : Fin n → ℝ => ∑ i, z i)
      (MeasureTheory.Measure.pi
        (fun i : Fin n => MeasureTheory.Measure.map (forwardLossValue (q i) (p i))
          (densityMeasure μ (q i)))) := by
        rw [hpi]
    _ =
    (PLDPair.compFamily (fun i : Fin n => concretePLDPair μ (p i) (q i))).reverse := by
      symm
      simpa [concretePLDPair, reverseLossLaw] using
        (PLDPair.compFamily_reverse_eq_pi_map_sum
          (L := fun i : Fin n => concretePLDPair μ (p i) (q i)))

/--
The concrete neighboring `PLDPair` of a finite heterogeneous shared-base
product density is exactly the composed `PLDPair.compFamily` of the coordinate
concrete pairs.
-/
theorem concretePLDPair_sharedBaseProduct_eq_compFamily
    {α : Type} [MeasurableSpace α]
    {n : ℕ}
    (μ : MeasureTheory.Measure α) [MeasureTheory.SigmaFinite μ]
    (p q : Fin n → α → ℝ)
    (hp_meas : ∀ i, Measurable (p i))
    (hq_meas : ∀ i, Measurable (q i))
    (hp_nonneg : ∀ i x, 0 ≤ p i x)
    (hq_nonneg : ∀ i x, 0 ≤ q i x)
    (hp_pos : ∀ i x, 0 < p i x)
    (hq_pos : ∀ i x, 0 < q i x)
    [∀ i : Fin n, MeasureTheory.IsFiniteMeasure (densityMeasure μ (p i))]
    [∀ i : Fin n, MeasureTheory.IsFiniteMeasure (densityMeasure μ (q i))] :
    concretePLDPair
      (MeasureTheory.Measure.pi (fun _ : Fin n => μ))
      (fun z : Fin n → α => ∏ i : Fin n, p i (z i))
      (fun z : Fin n → α => ∏ i : Fin n, q i (z i))
      =
    PLDPair.compFamily (fun i : Fin n => concretePLDPair μ (p i) (q i)) := by
  cases hleft :
      concretePLDPair
        (MeasureTheory.Measure.pi (fun _ : Fin n => μ))
        (fun z : Fin n → α => ∏ i : Fin n, p i (z i))
        (fun z : Fin n → α => ∏ i : Fin n, q i (z i)) with
  | mk lf lr =>
      cases hright : PLDPair.compFamily (fun i : Fin n => concretePLDPair μ (p i) (q i)) with
      | mk rf rr =>
          have hf : lf = rf := by
            simpa [hleft, hright] using
              (concretePLDPair_sharedBaseProduct_forward_eq_compFamily
                (μ := μ) (p := p) (q := q)
                (hp_meas := hp_meas) (hq_meas := hq_meas)
                (hp_nonneg := hp_nonneg) (hq_nonneg := hq_nonneg)
                (hp_pos := hp_pos) (hq_pos := hq_pos))
          have hr : lr = rr := by
            simpa [hleft, hright] using
              (concretePLDPair_sharedBaseProduct_reverse_eq_compFamily
                (μ := μ) (p := p) (q := q)
                (hp_meas := hp_meas) (hq_meas := hq_meas)
                (hp_nonneg := hp_nonneg) (hq_nonneg := hq_nonneg)
                (hp_pos := hp_pos) (hq_pos := hq_pos))
          cases hf
          cases hr
          rfl

/--
Shared-base density realization package for turning a concrete PLD profile bound
into event-level `ApproxDP`.
-/
structure ConcreteProfileApproxDPPackage
    {X Y : Type} [MeasurableSpace Y]
    (adj : X → X → Prop)
    (mech : X → MeasureTheory.Measure Y)
    (ε δ : ℝ) where
  baseMeasure : MeasureTheory.Measure Y
  dens : X → Y → ℝ
  delta_nonneg : 0 ≤ δ
  measurable : ∀ x, Measurable (dens x)
  integrable : ∀ x, MeasureTheory.Integrable (dens x) baseMeasure
  positive : ∀ x y, 0 < dens x y
  mech_eq : ∀ x, mech x = densityMeasure baseMeasure (dens x)
  profile_le : ∀ x x', adj x x' → (concretePLDPair baseMeasure (dens x) (dens x')).profile ε ≤ δ

/--
Exact heterogeneous-composition realization package.

This extends the concrete shared-base realization by recording that each
neighboring concrete PLD pair is exactly the composed `PLDPair.compFamily` of a
finite theorem-facing family.

Current honest boundary:
- the generic realization theorem for `concretePLDPair = PLDPair.compFamily`
  is landed below,
- but the profile-side field `composedProfile_le` is still external data,
- because the library does not yet expose a generic accountant theorem that
  derives a bound on `(PLDPair.compFamily ...).profile ε` from theorem-facing
  coordinate-family inputs.
-/
structure CompFamilyProfileApproxDPPackage
    {X Y : Type} [MeasurableSpace Y]
    (adj : X → X → Prop)
    (mech : X → MeasureTheory.Measure Y)
    (n : ℕ) (ε δ : ℝ) where
  concrete : ConcreteProfileApproxDPPackage adj mech ε δ
  pairFamily : X → X → Fin n → PLDPair
  compFamily_eq :
    ∀ x x', adj x x' →
      concretePLDPair concrete.baseMeasure (concrete.dens x) (concrete.dens x')
        = PLDPair.compFamily (pairFamily x x')
  composedProfile_le :
    ∀ x x', adj x x' → (PLDPair.compFamily (pairFamily x x')).profile ε ≤ δ

/--
Transport the concrete profile bound to the exact heterogeneous `compFamily`
profile surface using the realized PLD-pair equality.

This is the first exact bound layer available under
`CompFamilyProfileApproxDPPackage`: it does not derive the profile bound from
coordinate accountant inputs, but it does show that once the concrete
realization and concrete profile bound are known, the `compFamily` profile
bound is definitionally the same obligation.
-/
theorem compFamily_profile_le_of_compFamily_eq
    {X Y : Type} [MeasurableSpace Y]
    (adj : X → X → Prop)
    (mech : X → MeasureTheory.Measure Y)
    {n : ℕ} {ε δ : ℝ}
    (concrete : ConcreteProfileApproxDPPackage adj mech ε δ)
    (pairFamily : X → X → Fin n → PLDPair)
    (compFamily_eq :
      ∀ x x', adj x x' →
        concretePLDPair concrete.baseMeasure (concrete.dens x) (concrete.dens x')
          = PLDPair.compFamily (pairFamily x x')) :
    ∀ x x', adj x x' → (PLDPair.compFamily (pairFamily x x')).profile ε ≤ δ := by
  intro x x' hAdj
  simpa [← compFamily_eq x x' hAdj] using concrete.profile_le x x' hAdj

/--
Canonical constructor for `CompFamilyProfileApproxDPPackage` from the already
available concrete profile package and the exact `compFamily` realization.

This packages the exact equivalent composed-profile surface Lean can currently
realize generically: the missing `composedProfile_le` field is obtained by
transport from the concrete profile bound through `compFamily_eq`.

Current honest boundary:
- this constructor still assumes the concrete profile bound already exists,
- and the library still does not expose the lower accountant theorem that
  derives that concrete or composed profile bound from theorem-facing
  coordinate inputs.
-/
def CompFamilyProfileApproxDPPackage.ofConcrete
    {X Y : Type} [MeasurableSpace Y]
    (adj : X → X → Prop)
    (mech : X → MeasureTheory.Measure Y)
    {n : ℕ} {ε δ : ℝ}
    (concrete : ConcreteProfileApproxDPPackage adj mech ε δ)
    (pairFamily : X → X → Fin n → PLDPair)
    (compFamily_eq :
      ∀ x x', adj x x' →
        concretePLDPair concrete.baseMeasure (concrete.dens x) (concrete.dens x')
          = PLDPair.compFamily (pairFamily x x')) :
    CompFamilyProfileApproxDPPackage adj mech n ε δ where
  concrete := concrete
  pairFamily := pairFamily
  compFamily_eq := compFamily_eq
  composedProfile_le := compFamily_profile_le_of_compFamily_eq
    adj mech concrete pairFamily compFamily_eq

/--
Theorem-facing comparison/slack package beneath direct coordinate-input
accountant theorems for heterogeneous `PLDPair.compFamily`.

This records the strongest generic accountant object currently available below
the exact `compFamily` transport layer:
- a theorem-facing coordinate family of exact neighboring `PLDPair`s,
- a comparison profile surface,
- an explicit additive slack budget, and
- a pointwise bound from the exact composed profile to that comparison profile
  plus slack.

Current honest boundary:
- this package does not derive the comparison profile from coordinate inputs,
- and it does not yet collapse the comparison profile plus slack to a uniform
  scalar `δ` bound,
- but it gives downstream packets a named comparison surface that can be fed
  into later accountant theorems.
-/
structure CompFamilyCoordinateProfileComparisonPackage
    {X : Type}
    (adj : X → X → Prop)
    (n : ℕ) where
  pairFamily : X → X → Fin n → PLDPair
  comparisonProfile : X → X → ℝ → ℝ
  badSlack : ℝ
  profile_le :
    ∀ x x', adj x x' → ∀ ε,
      (PLDPair.compFamily (pairFamily x x')).profile ε
        ≤ comparisonProfile x x' ε + badSlack

namespace CompFamilyCoordinateProfileComparisonPackage

/-- Named conditional-comparison problem induced by one adjacent input pair. -/
def toConditionalProblem
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pkg : CompFamilyCoordinateProfileComparisonPackage adj n)
    (x x' : X) : ConditionalProfileComparisonProblem where
  targetProfile := fun ε => (PLDPair.compFamily (pkg.pairFamily x x')).profile ε
  comparisonProfile := pkg.comparisonProfile x x'
  badSlack := pkg.badSlack

@[simp] theorem toConditionalProblem_targetProfile
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pkg : CompFamilyCoordinateProfileComparisonPackage adj n)
    (x x' : X) (ε : ℝ) :
    (pkg.toConditionalProblem x x').targetProfile ε
      = (PLDPair.compFamily (pkg.pairFamily x x')).profile ε := by
  rfl

@[simp] theorem toConditionalProblem_comparisonProfile
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pkg : CompFamilyCoordinateProfileComparisonPackage adj n)
    (x x' : X) (ε : ℝ) :
    (pkg.toConditionalProblem x x').comparisonProfile ε
      = pkg.comparisonProfile x x' ε := by
  rfl

@[simp] theorem toConditionalProblem_badSlack
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pkg : CompFamilyCoordinateProfileComparisonPackage adj n)
    (x x' : X) :
    (pkg.toConditionalProblem x x').badSlack = pkg.badSlack := by
  rfl

/--
Exact composed-profile bound against the named slackened comparison profile for
one adjacent pair.
-/
theorem profile_le_slackenedComparison
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pkg : CompFamilyCoordinateProfileComparisonPackage adj n)
    {x x' : X}
    (hAdj : adj x x')
    {ε : ℝ} :
    (PLDPair.compFamily (pkg.pairFamily x x')).profile ε
      ≤ (pkg.toConditionalProblem x x').slackenedComparisonProfile ε := by
  refine (pkg.toConditionalProblem x x').target_le_slackened_of_le ?_
  simpa [toConditionalProblem] using pkg.profile_le x x' hAdj ε

/--
Pointwise consumer: once the named comparison profile plus slack is bounded by
`δ`, the exact composed profile is also bounded by `δ`.
-/
theorem profile_le_of_comparison_le
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pkg : CompFamilyCoordinateProfileComparisonPackage adj n)
    {x x' : X}
    (hAdj : adj x x')
    {ε δ : ℝ}
    (hCmp :
      pkg.comparisonProfile x x' ε + pkg.badSlack ≤ δ) :
    (PLDPair.compFamily (pkg.pairFamily x x')).profile ε ≤ δ := by
  calc
    (PLDPair.compFamily (pkg.pairFamily x x')).profile ε
      ≤ (pkg.toConditionalProblem x x').slackenedComparisonProfile ε :=
        pkg.profile_le_slackenedComparison hAdj
    _ = pkg.comparisonProfile x x' ε + pkg.badSlack := by
        simp [toConditionalProblem, ConditionalProfileComparisonProblem.slackenedComparisonProfile]
    _ ≤ δ := hCmp

/--
Uniform consumer theorem for filling the `composedProfile_le` field in later
`CompFamilyProfileApproxDPPackage` constructions.
-/
theorem profile_le_of_uniformComparisonLe
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pkg : CompFamilyCoordinateProfileComparisonPackage adj n)
    {ε δ : ℝ}
    (hCmp :
      ∀ x x', adj x x' →
        pkg.comparisonProfile x x' ε + pkg.badSlack ≤ δ) :
    ∀ x x', adj x x' →
      (PLDPair.compFamily (pkg.pairFamily x x')).profile ε ≤ δ := by
  intro x x' hAdj
  exact pkg.profile_le_of_comparison_le hAdj (hCmp x x' hAdj)

end CompFamilyCoordinateProfileComparisonPackage

namespace GaussianDP

/--
Generic GDP profile upper-bound package indexed by adjacent input pairs.

This is the strongest exact equivalent profile surface currently available
below the GDP tradeoff-comparison transport layer:
- each adjacent pair carries an exact heterogeneous `PLDPair` family,
- each adjacent pair also carries a candidate GDP parameter family, and
- the hypothesis is the exact-vs-GDP composed-profile inequality.

Current honest boundary:
- this package still does not derive that profile inequality from theorem-
  facing coordinate inputs,
- but it packages the exact lower profile surface that the landed
  `CoordinateCompFamilyTradeoffUpperBoundPackage.ofProfileLe` constructor
  consumes unchanged.
- it can also be built from the more primitive exact comparison/slack package
  surface plus a pointwise bound from that slackened comparison profile to the
  canonical GDP profile.
-/
structure CoordinateCompFamilyProfileUpperBoundPackage
    {X : Type}
    (adj : X → X → Prop)
    (n : ℕ) where
  pairFamily : X → X → Fin n → PLDPair
  μ : X → X → Fin n → ℝ
  profile_le :
    ∀ x x', adj x x' → ∀ ε : ℝ,
      (PLDPair.compFamily (pairFamily x x')).profile ε ≤
        (GaussianDP.compFamilyProfile (μ x x')).eval ε

/--
Generic GDP tradeoff-comparison package indexed by adjacent input pairs.

This is the upper transport layer above `GDPCompositionSurface.lean`:
- each adjacent pair carries an exact heterogeneous `PLDPair` family,
- each adjacent pair also carries a candidate GDP parameter family,
- and the hypothesis is the GDP-vs-exact tradeoff comparison on the landed
  exact `compFamilyTradeoffAt` surface.

The package itself is still exact and generic. It does not prove that the GDP
comparison hypothesis holds for any particular coordinate accountant family.
-/
structure CoordinateCompFamilyTradeoffUpperBoundPackage
    {X : Type}
    (adj : X → X → Prop)
    (n : ℕ) where
  pairFamily : X → X → Fin n → PLDPair
  μ : X → X → Fin n → ℝ
  tradeoff_le :
    ∀ x x', adj x x' → ∀ ε : ℝ,
      (GaussianDP.compFamilyTradeoffAt (μ x x') ε).PointwiseLE
        (PLDPair.compFamilyTradeoffAt (pairFamily x x') ε)

namespace CoordinateCompFamilyTradeoffUpperBoundPackage

/--
Constructor from the exact equivalent lower profile-comparison surface.

This is the theorem-facing coordinate form of
`GaussianDP.CompFamilyTradeoffUpperBoundPackage.ofProfileLe`: when a caller can
bound the exact heterogeneous composed profile by the canonical GDP profile for
each adjacent pair, the tradeoff-comparison package follows automatically on
the landed fixed-`ε` surfaces.
-/
def ofProfileLe
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pairFamily : X → X → Fin n → PLDPair)
    (μ : X → X → Fin n → ℝ)
    (hProfile :
      ∀ x x', adj x x' → ∀ ε : ℝ,
        (PLDPair.compFamily (pairFamily x x')).profile ε ≤
          (GaussianDP.compFamilyProfile (μ x x')).eval ε) :
    CoordinateCompFamilyTradeoffUpperBoundPackage adj n where
  pairFamily := pairFamily
  μ := μ
  tradeoff_le := by
    intro x x' hAdj
    exact compFamilyTradeoffAt_le_of_compFamilyProfile_le
      (hProfile x x' hAdj)

/--
Constructor from an exact witness family that composes through the landed
zero-slack represented monotonicity theorem.

This is the strongest exact equivalent GDP-family constructor currently
available above the represented layer:
- the witness family is already bounded by the canonical composed GDP profile,
- coordinatewise zero-slack realization domination maps that witness family
  into the target exact family,
- and the resulting GDP tradeoff package feeds the existing upper transport
  unchanged.
-/
def ofWitnessProfileLe_of_coordinateApproxRealizationDominates_zero_zero
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pairFamily witnessFamily : X → X → Fin n → PLDPair)
    (μ : X → X → Fin n → ℝ)
    [∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).forward)]
    [∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).reverse)]
    [∀ x x' i, MeasureTheory.IsFiniteMeasure ((witnessFamily x x' i).forward)]
    [∀ x x' i, MeasureTheory.IsFiniteMeasure ((witnessFamily x x' i).reverse)]
    (hDom :
      ∀ x x', adj x x' → ∀ i,
        (witnessFamily x x' i).ApproxRealizationDominates 0 0
          (pairFamily x x' i))
    (hProfile :
      ∀ x x', adj x x' → ∀ ε : ℝ,
        (PLDPair.compFamily (witnessFamily x x')).profile ε ≤
          (GaussianDP.compFamilyProfile (μ x x')).eval ε) :
    CoordinateCompFamilyTradeoffUpperBoundPackage adj n where
  pairFamily := pairFamily
  μ := μ
  tradeoff_le := by
    intro x x' hAdj ε
    exact
      GaussianDP.compFamilyTradeoffAt_le_of_witnessProfileLe_of_coordinateApproxRealizationDominates_zero_zero
        (pairFamily := pairFamily x x')
        (witnessFamily := witnessFamily x x')
        (μ := μ x x')
        (hDom x x' hAdj)
        (hProfile x x' hAdj) ε

@[simp] theorem ofWitnessProfileLe_of_coordinateApproxRealizationDominates_zero_zero_pairFamily
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pairFamily witnessFamily : X → X → Fin n → PLDPair)
    (μ : X → X → Fin n → ℝ)
    [∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).forward)]
    [∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).reverse)]
    [∀ x x' i, MeasureTheory.IsFiniteMeasure ((witnessFamily x x' i).forward)]
    [∀ x x' i, MeasureTheory.IsFiniteMeasure ((witnessFamily x x' i).reverse)]
    (hDom :
      ∀ x x', adj x x' → ∀ i,
        (witnessFamily x x' i).ApproxRealizationDominates 0 0
          (pairFamily x x' i))
    (hProfile :
      ∀ x x', adj x x' → ∀ ε : ℝ,
        (PLDPair.compFamily (witnessFamily x x')).profile ε ≤
          (GaussianDP.compFamilyProfile (μ x x')).eval ε) :
    (ofWitnessProfileLe_of_coordinateApproxRealizationDominates_zero_zero
      (adj := adj) (n := n) pairFamily witnessFamily μ hDom hProfile).pairFamily
      = pairFamily := rfl

@[simp] theorem ofWitnessProfileLe_of_coordinateApproxRealizationDominates_zero_zero_mu
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pairFamily witnessFamily : X → X → Fin n → PLDPair)
    (μ : X → X → Fin n → ℝ)
    [∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).forward)]
    [∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).reverse)]
    [∀ x x' i, MeasureTheory.IsFiniteMeasure ((witnessFamily x x' i).forward)]
    [∀ x x' i, MeasureTheory.IsFiniteMeasure ((witnessFamily x x' i).reverse)]
    (hDom :
      ∀ x x', adj x x' → ∀ i,
        (witnessFamily x x' i).ApproxRealizationDominates 0 0
          (pairFamily x x' i))
    (hProfile :
      ∀ x x', adj x x' → ∀ ε : ℝ,
        (PLDPair.compFamily (witnessFamily x x')).profile ε ≤
          (GaussianDP.compFamilyProfile (μ x x')).eval ε) :
    (ofWitnessProfileLe_of_coordinateApproxRealizationDominates_zero_zero
      (adj := adj) (n := n) pairFamily witnessFamily μ hDom hProfile).μ
      = μ := rfl

/--
Upper transport from the GDP tradeoff-comparison package to the landed exact
`CompFamilyCoordinateProfileComparisonPackage` surface.

The comparison profile is the canonical composed GDP profile and the slack is
exactly zero.

Current honest boundary:
- the tradeoff-facing hypothesis can now be built from the exact equivalent
  profile-facing inequality via `ofProfileLe`,
- so the remaining lower theorem seam is no longer tradeoff-shaped,
- it is the theorem deriving that exact-vs-GDP composed-profile inequality.
-/
def toProfileComparisonPackage
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pkg : CoordinateCompFamilyTradeoffUpperBoundPackage adj n) :
    CompFamilyCoordinateProfileComparisonPackage adj n where
  pairFamily := pkg.pairFamily
  comparisonProfile := fun x x' ε => (GaussianDP.compFamilyProfile (pkg.μ x x')).eval ε
  badSlack := 0
  profile_le := by
    intro x x' hAdj ε
    simpa using
      (GaussianDP.compFamilyProfile_le_of_compFamilyTradeoffAt_le
        (pkg.tradeoff_le x x' hAdj) ε)

@[simp] theorem toProfileComparisonPackage_pairFamily
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pkg : CoordinateCompFamilyTradeoffUpperBoundPackage adj n) :
    pkg.toProfileComparisonPackage.pairFamily = pkg.pairFamily := rfl

@[simp] theorem toProfileComparisonPackage_badSlack
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pkg : CoordinateCompFamilyTradeoffUpperBoundPackage adj n) :
    pkg.toProfileComparisonPackage.badSlack = 0 := rfl

@[simp] theorem toProfileComparisonPackage_comparisonProfile
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pkg : CoordinateCompFamilyTradeoffUpperBoundPackage adj n)
    (x x' : X) (ε : ℝ) :
    pkg.toProfileComparisonPackage.comparisonProfile x x' ε
      = (GaussianDP.compFamilyProfile (pkg.μ x x')).eval ε := rfl

/--
Uniform consumer theorem: a scalar bound on the canonical composed GDP profile
feeds directly into the exact composed-profile bound through the transported
comparison package.
-/
theorem profile_le_of_uniformGdpBound
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pkg : CoordinateCompFamilyTradeoffUpperBoundPackage adj n)
    {ε δ : ℝ}
    (hCmp :
      ∀ x x', adj x x' →
        (GaussianDP.compFamilyProfile (pkg.μ x x')).eval ε ≤ δ) :
    ∀ x x', adj x x' →
      (PLDPair.compFamily (pkg.pairFamily x x')).profile ε ≤ δ := by
  intro x x' hAdj
  have hCmp' :
      pkg.toProfileComparisonPackage.comparisonProfile x x' ε
        + pkg.toProfileComparisonPackage.badSlack ≤ δ := by
    simpa using hCmp x x' hAdj
  exact pkg.toProfileComparisonPackage.profile_le_of_comparison_le hAdj hCmp'

end CoordinateCompFamilyTradeoffUpperBoundPackage

/--
Exact `PLDPair` witness representation beneath the witness-bridge package.

This is the sharpest honest lower representation surface currently available
for the generic coordinate-GDP route:
- the target exact family is fixed externally,
- the witness family and candidate GDP parameters remain explicit,
- and only the exact witness-side data is stored here.

Current honest boundary:
- this surface still does not canonically derive the witness family from bare
  coordinate GDP profile inputs by itself,
- but it cleanly isolates the exact witness representation from the larger
  package that also stores target-family finiteness data.
-/
structure CoordinateCompFamilyExactWitnessRepresentation
    {X : Type}
    (adj : X → X → Prop)
    (n : ℕ)
    (pairFamily : X → X → Fin n → PLDPair) where
  witnessFamily : X → X → Fin n → PLDPair
  μ : X → X → Fin n → ℝ
  witnessForward_finite :
    ∀ x x' i, MeasureTheory.IsFiniteMeasure ((witnessFamily x x' i).forward)
  witnessReverse_finite :
    ∀ x x' i, MeasureTheory.IsFiniteMeasure ((witnessFamily x x' i).reverse)
  hDom :
    ∀ x x', adj x x' → ∀ i,
      (witnessFamily x x' i).ApproxRealizationDominates 0 0
        (pairFamily x x' i)
  hProfile :
    ∀ x x', adj x x' → ∀ ε : ℝ,
      (PLDPair.compFamily (witnessFamily x x')).profile ε ≤
        (GaussianDP.compFamilyProfile (μ x x')).eval ε

namespace CoordinateCompFamilyExactWitnessRepresentation

/--
Theorem-facing constructor from the bare witness-side coordinate GDP inputs.

This is the honest lower constructor surface for the generic GDP route:
- the caller still exhibits the exact target family and witness family,
- coordinatewise zero-slack domination remains explicit,
- and the only GDP-side hypothesis is the composed witness-profile bound
  against the canonical heterogeneous GDP profile.

What lands here is not a canonical derivation of the witness family from GDP
inputs alone. It is the exact representation package built directly from the
explicit witness-side data that the generic upper route already consumes.
-/
def ofWitnessProfileLe_of_coordinateApproxRealizationDominates_zero_zero
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pairFamily witnessFamily : X → X → Fin n → PLDPair)
    (μ : X → X → Fin n → ℝ)
    [∀ x x' i, MeasureTheory.IsFiniteMeasure ((witnessFamily x x' i).forward)]
    [∀ x x' i, MeasureTheory.IsFiniteMeasure ((witnessFamily x x' i).reverse)]
    (hDom :
      ∀ x x', adj x x' → ∀ i,
        (witnessFamily x x' i).ApproxRealizationDominates 0 0
          (pairFamily x x' i))
    (hProfile :
      ∀ x x', adj x x' → ∀ ε : ℝ,
        (PLDPair.compFamily (witnessFamily x x')).profile ε ≤
          (GaussianDP.compFamilyProfile (μ x x')).eval ε) :
    CoordinateCompFamilyExactWitnessRepresentation adj n pairFamily where
  witnessFamily := witnessFamily
  μ := μ
  witnessForward_finite := by
    intro x x' i
    infer_instance
  witnessReverse_finite := by
    intro x x' i
    infer_instance
  hDom := hDom
  hProfile := hProfile

@[simp] theorem ofWitnessProfileLe_of_coordinateApproxRealizationDominates_zero_zero_witnessFamily
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pairFamily witnessFamily : X → X → Fin n → PLDPair)
    (μ : X → X → Fin n → ℝ)
    [∀ x x' i, MeasureTheory.IsFiniteMeasure ((witnessFamily x x' i).forward)]
    [∀ x x' i, MeasureTheory.IsFiniteMeasure ((witnessFamily x x' i).reverse)]
    (hDom :
      ∀ x x', adj x x' → ∀ i,
        (witnessFamily x x' i).ApproxRealizationDominates 0 0
          (pairFamily x x' i))
    (hProfile :
      ∀ x x', adj x x' → ∀ ε : ℝ,
        (PLDPair.compFamily (witnessFamily x x')).profile ε ≤
          (GaussianDP.compFamilyProfile (μ x x')).eval ε) :
    (ofWitnessProfileLe_of_coordinateApproxRealizationDominates_zero_zero
      (adj := adj) (n := n) pairFamily witnessFamily μ hDom hProfile).witnessFamily
      = witnessFamily := rfl

@[simp] theorem ofWitnessProfileLe_of_coordinateApproxRealizationDominates_zero_zero_mu
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pairFamily witnessFamily : X → X → Fin n → PLDPair)
    (μ : X → X → Fin n → ℝ)
    [∀ x x' i, MeasureTheory.IsFiniteMeasure ((witnessFamily x x' i).forward)]
    [∀ x x' i, MeasureTheory.IsFiniteMeasure ((witnessFamily x x' i).reverse)]
    (hDom :
      ∀ x x', adj x x' → ∀ i,
        (witnessFamily x x' i).ApproxRealizationDominates 0 0
          (pairFamily x x' i))
    (hProfile :
      ∀ x x', adj x x' → ∀ ε : ℝ,
        (PLDPair.compFamily (witnessFamily x x')).profile ε ≤
          (GaussianDP.compFamilyProfile (μ x x')).eval ε) :
    (ofWitnessProfileLe_of_coordinateApproxRealizationDominates_zero_zero
      (adj := adj) (n := n) pairFamily witnessFamily μ hDom hProfile).μ
      = μ := rfl

end CoordinateCompFamilyExactWitnessRepresentation

/--
Exact-equivalent witness-family bridge package beneath the coordinate GDP
transport layer.

This is the strongest honest generic surface currently available for the
"raw coordinate GDP inputs -> witness-family assumptions" seam:
- it keeps the target exact family explicit,
- it carries the witness family and candidate GDP parameters explicitly,
- and it stores exactly the lower assumptions already known to be sufficient
  for the archived witness-family theorem.

Current honest boundary:
- this package does not canonically construct the witness family from bare
  coordinate GDP profile inputs by itself,
- but it packages the exact lower bridge data without adding another opaque
  upper comparison layer.
-/
structure CoordinateCompFamilyWitnessBridgePackage
    {X : Type}
    (adj : X → X → Prop)
    (n : ℕ) where
  pairFamily : X → X → Fin n → PLDPair
  witnessFamily : X → X → Fin n → PLDPair
  μ : X → X → Fin n → ℝ
  pairForward_finite :
    ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).forward)
  pairReverse_finite :
    ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).reverse)
  witnessForward_finite :
    ∀ x x' i, MeasureTheory.IsFiniteMeasure ((witnessFamily x x' i).forward)
  witnessReverse_finite :
    ∀ x x' i, MeasureTheory.IsFiniteMeasure ((witnessFamily x x' i).reverse)
  hDom :
    ∀ x x', adj x x' → ∀ i,
      (witnessFamily x x' i).ApproxRealizationDominates 0 0
        (pairFamily x x' i)
  hProfile :
    ∀ x x', adj x x' → ∀ ε : ℝ,
      (PLDPair.compFamily (witnessFamily x x')).profile ε ≤
        (GaussianDP.compFamilyProfile (μ x x')).eval ε

/--
Promote the lower exact witness representation to the landed witness-bridge
package once target-family finiteness data is supplied.
-/
def CoordinateCompFamilyExactWitnessRepresentation.toWitnessBridgePackage
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    {pairFamily : X → X → Fin n → PLDPair}
    (repr : CoordinateCompFamilyExactWitnessRepresentation adj n pairFamily)
    (pairForward_finite :
      ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).forward))
    (pairReverse_finite :
      ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).reverse)) :
    CoordinateCompFamilyWitnessBridgePackage adj n where
  pairFamily := pairFamily
  witnessFamily := repr.witnessFamily
  μ := repr.μ
  pairForward_finite := pairForward_finite
  pairReverse_finite := pairReverse_finite
  witnessForward_finite := repr.witnessForward_finite
  witnessReverse_finite := repr.witnessReverse_finite
  hDom := repr.hDom
  hProfile := repr.hProfile

/--
Minimal wrapper from the exact witness representation surface into the landed
package API.
-/
def CoordinateCompFamilyWitnessBridgePackage.ofExactWitnessRepresentation
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    {pairFamily : X → X → Fin n → PLDPair}
    (repr : CoordinateCompFamilyExactWitnessRepresentation adj n pairFamily)
    (pairForward_finite :
      ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).forward))
    (pairReverse_finite :
      ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).reverse)) :
    CoordinateCompFamilyWitnessBridgePackage adj n :=
  repr.toWitnessBridgePackage pairForward_finite pairReverse_finite

/--
Direct wrapper from the bare witness-side coordinate GDP inputs into the
landed witness-bridge package.

This is the public theorem-facing constructor above the exact witness
representation surface. It does not add any new comparison layer; it just
packages the explicit witness-side data into the existing bridge object.
-/
def CoordinateCompFamilyWitnessBridgePackage.ofWitnessProfileLe_of_coordinateApproxRealizationDominates_zero_zero
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pairFamily witnessFamily : X → X → Fin n → PLDPair)
    (μ : X → X → Fin n → ℝ)
    [∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).forward)]
    [∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).reverse)]
    [∀ x x' i, MeasureTheory.IsFiniteMeasure ((witnessFamily x x' i).forward)]
    [∀ x x' i, MeasureTheory.IsFiniteMeasure ((witnessFamily x x' i).reverse)]
    (hDom :
      ∀ x x', adj x x' → ∀ i,
        (witnessFamily x x' i).ApproxRealizationDominates 0 0
          (pairFamily x x' i))
    (hProfile :
      ∀ x x', adj x x' → ∀ ε : ℝ,
        (PLDPair.compFamily (witnessFamily x x')).profile ε ≤
          (GaussianDP.compFamilyProfile (μ x x')).eval ε) :
    CoordinateCompFamilyWitnessBridgePackage adj n :=
  CoordinateCompFamilyWitnessBridgePackage.ofExactWitnessRepresentation
    (CoordinateCompFamilyExactWitnessRepresentation.ofWitnessProfileLe_of_coordinateApproxRealizationDominates_zero_zero
      (adj := adj) (n := n) pairFamily witnessFamily μ hDom hProfile)
    (pairForward_finite := by
      intro x x' i
      infer_instance)
    (pairReverse_finite := by
      intro x x' i
      infer_instance)

/--
The exact-equivalent witness bridge package feeds the landed coordinate GDP
tradeoff constructor without any additional data.
-/
def CoordinateCompFamilyWitnessBridgePackage.toTradeoffPackage
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pkg : CoordinateCompFamilyWitnessBridgePackage adj n) :
    CoordinateCompFamilyTradeoffUpperBoundPackage adj n := by
  letI : ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pkg.pairFamily x x' i).forward) :=
    pkg.pairForward_finite
  letI : ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pkg.pairFamily x x' i).reverse) :=
    pkg.pairReverse_finite
  letI : ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pkg.witnessFamily x x' i).forward) :=
    pkg.witnessForward_finite
  letI : ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pkg.witnessFamily x x' i).reverse) :=
    pkg.witnessReverse_finite
  exact
    CoordinateCompFamilyTradeoffUpperBoundPackage.ofWitnessProfileLe_of_coordinateApproxRealizationDominates_zero_zero
      (adj := adj) (n := n)
      pkg.pairFamily pkg.witnessFamily pkg.μ pkg.hDom pkg.hProfile

@[simp] theorem CoordinateCompFamilyWitnessBridgePackage.toTradeoffPackage_pairFamily
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pkg : CoordinateCompFamilyWitnessBridgePackage adj n) :
    pkg.toTradeoffPackage.pairFamily = pkg.pairFamily := by
  letI : ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pkg.pairFamily x x' i).forward) :=
    pkg.pairForward_finite
  letI : ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pkg.pairFamily x x' i).reverse) :=
    pkg.pairReverse_finite
  letI : ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pkg.witnessFamily x x' i).forward) :=
    pkg.witnessForward_finite
  letI : ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pkg.witnessFamily x x' i).reverse) :=
    pkg.witnessReverse_finite
  simpa [CoordinateCompFamilyWitnessBridgePackage.toTradeoffPackage] using
    (CoordinateCompFamilyTradeoffUpperBoundPackage.ofWitnessProfileLe_of_coordinateApproxRealizationDominates_zero_zero_pairFamily
      (adj := adj) (n := n)
      pkg.pairFamily pkg.witnessFamily pkg.μ pkg.hDom pkg.hProfile)

@[simp] theorem CoordinateCompFamilyWitnessBridgePackage.toTradeoffPackage_mu
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pkg : CoordinateCompFamilyWitnessBridgePackage adj n) :
    pkg.toTradeoffPackage.μ = pkg.μ := by
  letI : ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pkg.pairFamily x x' i).forward) :=
    pkg.pairForward_finite
  letI : ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pkg.pairFamily x x' i).reverse) :=
    pkg.pairReverse_finite
  letI : ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pkg.witnessFamily x x' i).forward) :=
    pkg.witnessForward_finite
  letI : ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pkg.witnessFamily x x' i).reverse) :=
    pkg.witnessReverse_finite
  simpa [CoordinateCompFamilyWitnessBridgePackage.toTradeoffPackage] using
    (CoordinateCompFamilyTradeoffUpperBoundPackage.ofWitnessProfileLe_of_coordinateApproxRealizationDominates_zero_zero_mu
      (adj := adj) (n := n)
      pkg.pairFamily pkg.witnessFamily pkg.μ pkg.hDom pkg.hProfile)

/--
Minimal wrapper from the exact-equivalent witness bridge package into the
landed profile-comparison package consumed further upstream.
-/
def CoordinateCompFamilyWitnessBridgePackage.toProfileComparisonPackage
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pkg : CoordinateCompFamilyWitnessBridgePackage adj n) :
    CompFamilyCoordinateProfileComparisonPackage adj n :=
  pkg.toTradeoffPackage.toProfileComparisonPackage

/--
The exact witness representation feeds the landed GDP tradeoff package through
the existing witness-bridge route, with no extra comparison layer inserted.
-/
def CoordinateCompFamilyExactWitnessRepresentation.toTradeoffPackage
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    {pairFamily : X → X → Fin n → PLDPair}
    (repr : CoordinateCompFamilyExactWitnessRepresentation adj n pairFamily)
    (pairForward_finite :
      ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).forward))
    (pairReverse_finite :
      ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).reverse)) :
    CoordinateCompFamilyTradeoffUpperBoundPackage adj n :=
  (repr.toWitnessBridgePackage pairForward_finite pairReverse_finite).toTradeoffPackage

/--
The exact witness representation also feeds the landed exact profile-comparison
package through the same route.
-/
def CoordinateCompFamilyExactWitnessRepresentation.toProfileComparisonPackage
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    {pairFamily : X → X → Fin n → PLDPair}
    (repr : CoordinateCompFamilyExactWitnessRepresentation adj n pairFamily)
    (pairForward_finite :
      ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).forward))
    (pairReverse_finite :
      ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).reverse)) :
    CompFamilyCoordinateProfileComparisonPackage adj n :=
  (repr.toWitnessBridgePackage pairForward_finite pairReverse_finite).toProfileComparisonPackage

@[simp] theorem CoordinateCompFamilyExactWitnessRepresentation.toTradeoffPackage_pairFamily
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    {pairFamily : X → X → Fin n → PLDPair}
    (repr : CoordinateCompFamilyExactWitnessRepresentation adj n pairFamily)
    (pairForward_finite :
      ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).forward))
    (pairReverse_finite :
      ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).reverse)) :
    (repr.toTradeoffPackage pairForward_finite pairReverse_finite).pairFamily = pairFamily := by
  rw [CoordinateCompFamilyExactWitnessRepresentation.toTradeoffPackage]
  rw [CoordinateCompFamilyWitnessBridgePackage.toTradeoffPackage_pairFamily]
  rfl

@[simp] theorem CoordinateCompFamilyExactWitnessRepresentation.toTradeoffPackage_mu
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    {pairFamily : X → X → Fin n → PLDPair}
    (repr : CoordinateCompFamilyExactWitnessRepresentation adj n pairFamily)
    (pairForward_finite :
      ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).forward))
    (pairReverse_finite :
      ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).reverse)) :
    (repr.toTradeoffPackage pairForward_finite pairReverse_finite).μ = repr.μ := by
  rw [CoordinateCompFamilyExactWitnessRepresentation.toTradeoffPackage]
  rw [CoordinateCompFamilyWitnessBridgePackage.toTradeoffPackage_mu]
  rfl

@[simp] theorem CoordinateCompFamilyExactWitnessRepresentation.toWitnessBridgePackage_pairFamily
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    {pairFamily : X → X → Fin n → PLDPair}
    (repr : CoordinateCompFamilyExactWitnessRepresentation adj n pairFamily)
    (pairForward_finite :
      ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).forward))
    (pairReverse_finite :
      ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).reverse)) :
    (repr.toWitnessBridgePackage pairForward_finite pairReverse_finite).pairFamily = pairFamily :=
  rfl

@[simp] theorem CoordinateCompFamilyExactWitnessRepresentation.toWitnessBridgePackage_witnessFamily
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    {pairFamily : X → X → Fin n → PLDPair}
    (repr : CoordinateCompFamilyExactWitnessRepresentation adj n pairFamily)
    (pairForward_finite :
      ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).forward))
    (pairReverse_finite :
      ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).reverse)) :
    (repr.toWitnessBridgePackage pairForward_finite pairReverse_finite).witnessFamily
      = repr.witnessFamily :=
  rfl

@[simp] theorem CoordinateCompFamilyExactWitnessRepresentation.toWitnessBridgePackage_mu
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    {pairFamily : X → X → Fin n → PLDPair}
    (repr : CoordinateCompFamilyExactWitnessRepresentation adj n pairFamily)
    (pairForward_finite :
      ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).forward))
    (pairReverse_finite :
      ∀ x x' i, MeasureTheory.IsFiniteMeasure ((pairFamily x x' i).reverse)) :
    (repr.toWitnessBridgePackage pairForward_finite pairReverse_finite).μ = repr.μ :=
  rfl

namespace CoordinateCompFamilyProfileUpperBoundPackage

/--
Constructor from the generic exact comparison/slack package plus a pointwise
comparison-to-GDP bound.

This is the strongest exact equivalent lower profile surface currently exposed
below the GDP profile package: once a caller has an exact `compFamily` profile
comparison package and can bound its slackened comparison profile by the
canonical GDP profile, the `profile_le` field follows immediately.
-/
def ofComparisonPackage
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pkg : CompFamilyCoordinateProfileComparisonPackage adj n)
    (μ : X → X → Fin n → ℝ)
    (hCmp :
      ∀ x x', adj x x' → ∀ ε : ℝ,
        pkg.comparisonProfile x x' ε + pkg.badSlack ≤
          (GaussianDP.compFamilyProfile (μ x x')).eval ε) :
    CoordinateCompFamilyProfileUpperBoundPackage adj n where
  pairFamily := pkg.pairFamily
  μ := μ
  profile_le := by
    intro x x' hAdj ε
    exact pkg.profile_le_of_comparison_le hAdj (hCmp x x' hAdj ε)

@[simp] theorem ofComparisonPackage_pairFamily
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pkg : CompFamilyCoordinateProfileComparisonPackage adj n)
    (μ : X → X → Fin n → ℝ)
    (hCmp :
      ∀ x x', adj x x' → ∀ ε : ℝ,
        pkg.comparisonProfile x x' ε + pkg.badSlack ≤
          (GaussianDP.compFamilyProfile (μ x x')).eval ε) :
    (ofComparisonPackage pkg μ hCmp).pairFamily = pkg.pairFamily := rfl

@[simp] theorem ofComparisonPackage_mu
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pkg : CompFamilyCoordinateProfileComparisonPackage adj n)
    (μ : X → X → Fin n → ℝ)
    (hCmp :
      ∀ x x', adj x x' → ∀ ε : ℝ,
        pkg.comparisonProfile x x' ε + pkg.badSlack ≤
          (GaussianDP.compFamilyProfile (μ x x')).eval ε) :
    (ofComparisonPackage pkg μ hCmp).μ = μ := rfl

/--
Transport the exact lower profile surface to the landed GDP tradeoff package.
-/
def toTradeoffPackage
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pkg : CoordinateCompFamilyProfileUpperBoundPackage adj n) :
    CoordinateCompFamilyTradeoffUpperBoundPackage adj n :=
  CoordinateCompFamilyTradeoffUpperBoundPackage.ofProfileLe
    pkg.pairFamily pkg.μ pkg.profile_le

@[simp] theorem toTradeoffPackage_pairFamily
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pkg : CoordinateCompFamilyProfileUpperBoundPackage adj n) :
    pkg.toTradeoffPackage.pairFamily = pkg.pairFamily := rfl

@[simp] theorem toTradeoffPackage_mu
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pkg : CoordinateCompFamilyProfileUpperBoundPackage adj n) :
    pkg.toTradeoffPackage.μ = pkg.μ := rfl

/--
Transport the exact lower profile surface all the way to the landed exact
comparison-package surface.
-/
def toProfileComparisonPackage
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pkg : CoordinateCompFamilyProfileUpperBoundPackage adj n) :
    CompFamilyCoordinateProfileComparisonPackage adj n :=
  pkg.toTradeoffPackage.toProfileComparisonPackage

/--
Uniform consumer theorem on the exact lower profile surface.
-/
theorem profile_le_of_uniformGdpBound
    {X : Type}
    {adj : X → X → Prop}
    {n : ℕ}
    (pkg : CoordinateCompFamilyProfileUpperBoundPackage adj n)
    {ε δ : ℝ}
    (hCmp :
      ∀ x x', adj x x' →
        (GaussianDP.compFamilyProfile (pkg.μ x x')).eval ε ≤ δ) :
    ∀ x x', adj x x' →
      (PLDPair.compFamily (pkg.pairFamily x x')).profile ε ≤ δ := by
  intro x x' hAdj
  exact pkg.toTradeoffPackage.profile_le_of_uniformGdpBound hCmp x x' hAdj

end CoordinateCompFamilyProfileUpperBoundPackage

end GaussianDP

private theorem concrete_profile_eq_privacyLossGap
    {Y : Type} [MeasurableSpace Y]
    (μ : MeasureTheory.Measure Y) (p q : Y → ℝ) (ε : ℝ)
    (hp_meas : Measurable p) (hq_meas : Measurable q)
    (hp_pos : ∀ y, 0 < p y) (hq_pos : ∀ y, 0 < q y) :
    (concretePLDPair μ p q).profile ε =
      ∫ y in posRegion (fun z => p z - Real.exp ε * q z),
        (p y - Real.exp ε * q y) ∂μ := by
  have hpos_meas : MeasurableSet (posRegion (fun z => p z - Real.exp ε * q z)) := by
    change MeasurableSet {y | 0 ≤ p y - Real.exp ε * q y}
    exact measurableSet_le measurable_const (hp_meas.sub (hq_meas.const_mul (Real.exp ε)))
  have hEqInt :
      (∫ y, sourceHockeyStickGapIntegrand ε p q y ∂μ)
        =
      ∫ y in posRegion (fun z => p z - Real.exp ε * q z),
        (p y - Real.exp ε * q y) ∂μ := by
    have hfun :
        (fun y => sourceHockeyStickGapIntegrand ε p q y)
          =
        Set.indicator (posRegion (fun z => p z - Real.exp ε * q z))
          (fun y => p y - Real.exp ε * q y) := by
      funext y
      by_cases hy : Real.exp ε * q y ≤ p y
      · have hy' : 0 ≤ p y - Real.exp ε * q y := by linarith
        simp [sourceHockeyStickGapIntegrand, posRegion, hy, hy']
      · have hy' : ¬ 0 ≤ p y - Real.exp ε * q y := by linarith
        simp [sourceHockeyStickGapIntegrand, posRegion, hy,
          max_eq_right (le_of_not_ge hy')]
    rw [hfun, MeasureTheory.integral_indicator hpos_meas]
  rw [PLDPair.profile, concretePLDPair, forwardLossLaw]
  rw [expHockeyStickLaw_densityMeasure_map_forwardLossValue_eq_integral_gap_local
    (μ := μ) (f := p) (g := q) (ε := ε) hp_meas hq_meas hp_pos hq_pos]
  exact hEqInt

/--
Generic bridge from a concrete shared-base PLD profile bound to event-level
`ApproxDP`.
-/
theorem approxDP_of_concreteProfileBoundPackage
    {X Y : Type} [MeasurableSpace Y]
    (adj : X → X → Prop)
    (mech : X → MeasureTheory.Measure Y)
    {ε δ : ℝ}
    (pkg : ConcreteProfileApproxDPPackage adj mech ε δ) :
    ApproxDP adj mech ε δ := by
  have hDensity :
      ApproxDP adj
        (fun x => densityMeasure pkg.baseMeasure (pkg.dens x))
        ε δ := by
    apply approxDP_of_withDensity_privacyLossSet_bound
      (adj := adj) (μ := pkg.baseMeasure) (dens := pkg.dens)
      pkg.delta_nonneg pkg.measurable pkg.integrable
    · intro x y
      exact le_of_lt (pkg.positive x y)
    · intro x x' hAdj
      have hprof := pkg.profile_le x x' hAdj
      rw [concrete_profile_eq_privacyLossGap
        (μ := pkg.baseMeasure) (p := pkg.dens x) (q := pkg.dens x') (ε := ε)
        (hp_meas := pkg.measurable x) (hq_meas := pkg.measurable x')
        (hp_pos := pkg.positive x) (hq_pos := pkg.positive x')] at hprof
      exact hprof
  intro x x' hAdj s hs
  simpa [pkg.mech_eq x, pkg.mech_eq x'] using hDensity x x' hAdj s hs

/--
Profile-to-`ApproxDP` bridge on the theorem-facing heterogeneous
`PLDPair.compFamily` surface.

This consumer theorem is downstream of the still-missing accountant theorem
supplying `pkg.composedProfile_le`.
-/
theorem approxDP_of_compFamilyProfileBoundPackage
    {X Y : Type} [MeasurableSpace Y]
    (adj : X → X → Prop)
    (mech : X → MeasureTheory.Measure Y)
    {n : ℕ} {ε δ : ℝ}
    (pkg : CompFamilyProfileApproxDPPackage adj mech n ε δ) :
    ApproxDP adj mech ε δ := by
  let concretePkg : ConcreteProfileApproxDPPackage adj mech ε δ :=
    { pkg.concrete with
      profile_le := by
        intro x x' hAdj
        have hprof := pkg.composedProfile_le x x' hAdj
        simpa [pkg.compFamily_eq x x' hAdj] using hprof }
  exact approxDP_of_concreteProfileBoundPackage adj mech concretePkg

end
end DP
end Mf
