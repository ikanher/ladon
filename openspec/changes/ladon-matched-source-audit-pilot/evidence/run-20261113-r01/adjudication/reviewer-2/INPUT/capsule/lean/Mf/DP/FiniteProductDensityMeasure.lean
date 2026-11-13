import Mf.DP.PLDRandomAllocation

/-!
# Finite products of density measures

This lightweight owner isolates the product-density identity needed by the
sampled-Gaussian chi-square development.  It deliberately avoids importing
the numerical PLD composition surface.
-/

namespace Mf.DP

noncomputable section

private theorem map_densityMeasure_measurableEquiv_light
    {α β : Type} [MeasurableSpace α] [MeasurableSpace β]
    (e : α ≃ᵐ β)
    (μ : MeasureTheory.Measure α) (f : β → ℝ) :
    MeasureTheory.Measure.map e (densityMeasure μ (f ∘ e)) =
      densityMeasure (MeasureTheory.Measure.map e μ) f := by
  ext s hs
  rw [densityMeasure, densityMeasure, MeasurableEquiv.map_apply,
    MeasureTheory.withDensity_apply _ (e.measurable hs),
    MeasureTheory.withDensity_apply _ hs]
  calc
    ∫⁻ a in e ⁻¹' s, ENNReal.ofReal (f (e a)) ∂μ =
        ∫⁻ a, Set.indicator (e ⁻¹' s)
          (fun a => ENNReal.ofReal (f (e a))) a ∂μ := by
      rw [MeasureTheory.lintegral_indicator (e.measurable hs)]
    _ = ∫⁻ a, Set.indicator s (fun b => ENNReal.ofReal (f b)) (e a) ∂μ := by
      refine MeasureTheory.lintegral_congr_ae ?_
      filter_upwards with a
      by_cases ha : e a ∈ s <;> simp [ha]
    _ = ∫⁻ b, Set.indicator s (fun b => ENNReal.ofReal (f b)) b
          ∂MeasureTheory.Measure.map e μ := by
      simpa using
        (MeasureTheory.lintegral_map_equiv
          (μ := μ) (g := e)
          (f := Set.indicator s (fun b => ENNReal.ofReal (f b)))).symm
    _ = ∫⁻ b in s, ENNReal.ofReal (f b)
          ∂MeasureTheory.Measure.map e μ := by
      rw [MeasureTheory.lintegral_indicator hs]

/-- A finite product of densities against a common base measure is the density
of the coordinatewise product against the product base measure. -/
theorem finiteProductDensityMeasure_eq
    {β : Type} [MeasurableSpace β]
    (ν : MeasureTheory.Measure β) [MeasureTheory.SigmaFinite ν]
    (f : (i : Fin n) → β → ℝ)
    (hf_meas : ∀ i, Measurable (f i))
    (hf_nonneg : ∀ i x, 0 ≤ f i x) :
    densityMeasure
        (MeasureTheory.Measure.pi (fun _ : Fin n => ν))
        (fun z : Fin n → β => ∏ i : Fin n, f i (z i)) =
      MeasureTheory.Measure.pi (fun i : Fin n => densityMeasure ν (f i)) := by
  induction n with
  | zero =>
      let e := MeasurableEquiv.ofUniqueOfUnique (Fin 0 → β) Unit
      apply (e.measurableEmbedding.map_injective)
      calc
        MeasureTheory.Measure.map e
            (densityMeasure
              (MeasureTheory.Measure.pi (fun _ : Fin 0 => ν))
              (fun z : Fin 0 → β => ∏ i : Fin 0, f i (z i))) =
          MeasureTheory.Measure.map e
            (MeasureTheory.Measure.pi (fun _ : Fin 0 => ν)) := by
          simp [densityMeasure]
        _ = MeasureTheory.Measure.dirac () := by
          simpa [e] using
            (MeasureTheory.measurePreserving_pi_empty
              (μ := fun _ : Fin 0 => ν)).map_eq
        _ = MeasureTheory.Measure.map e
            (MeasureTheory.Measure.pi
              (fun i : Fin 0 => densityMeasure ν (f i))) := by
          symm
          simpa [e] using
            (MeasureTheory.measurePreserving_pi_empty
              (μ := fun i : Fin 0 => densityMeasure ν (f i))).map_eq
  | succ n ih =>
      let e := MeasurableEquiv.piFinSuccAbove
        (fun _ : Fin (n + 1) => β) (Fin.last n)
      let g : β × (Fin n → β) → ℝ :=
        fun z => f (Fin.last n) z.1 * ∏ i : Fin n, f i.castSucc (z.2 i)
      have hcomp : g ∘ e =
          fun x : Fin (n + 1) → β => ∏ i : Fin (n + 1), f i (x i) := by
        funext x
        have hlast : (e x).1 = x (Fin.last n) := by simp [e]
        have htail : ∀ i : Fin n, (e x).2 i = x i.castSucc := by
          intro i
          have hinit : Fin.init x i = x i.castSucc := by
            simpa using congrFun (Fin.snoc_init_self x) i.castSucc
          simpa [e] using hinit
        calc
          g (e x) = f (Fin.last n) ((e x).1) *
              ∏ i : Fin n, f i.castSucc ((e x).2 i) := by simp [g]
          _ = f (Fin.last n) (x (Fin.last n)) *
              ∏ i : Fin n, f i.castSucc (x i.castSucc) := by
            rw [hlast]
            congr
            funext i
            simpa [htail i]
          _ = ∏ i : Fin (n + 1), f i (x i) := by
            rw [← Fin.snoc_init_self x, Fin.prod_univ_castSucc]
            simp [Fin.snoc_castSucc, Fin.snoc_last, mul_comm]
      apply (e.measurableEmbedding.map_injective)
      calc
        MeasureTheory.Measure.map e
            (densityMeasure
              (MeasureTheory.Measure.pi (fun _ : Fin (n + 1) => ν))
              (fun z : Fin (n + 1) → β => ∏ i : Fin (n + 1), f i (z i))) =
          densityMeasure
            (MeasureTheory.Measure.map e
              (MeasureTheory.Measure.pi (fun _ : Fin (n + 1) => ν))) g := by
          simpa [hcomp] using
            (map_densityMeasure_measurableEquiv_light e
              (MeasureTheory.Measure.pi (fun _ : Fin (n + 1) => ν)) g)
        _ = densityMeasure
            (ν.prod (MeasureTheory.Measure.pi (fun i : Fin n => ν))) g := by
          rw [show MeasureTheory.Measure.map e
              (MeasureTheory.Measure.pi (fun _ : Fin (n + 1) => ν)) =
                ν.prod (MeasureTheory.Measure.pi (fun i : Fin n => ν)) by
            simpa [e] using
              (MeasureTheory.measurePreserving_piFinSuccAbove
                (μ := fun _ : Fin (n + 1) => ν) (i := Fin.last n)).map_eq]
        _ = (densityMeasure ν (f (Fin.last n))).prod
            (densityMeasure
              (MeasureTheory.Measure.pi (fun i : Fin n => ν))
              (fun z : Fin n → β => ∏ i : Fin n, f i.castSucc (z i))) := by
          unfold densityMeasure g
          have hmul :
              (fun z : β × (Fin n → β) => ENNReal.ofReal
                (f (Fin.last n) z.1 *
                  ∏ i : Fin n, f i.castSucc (z.2 i))) =
                (fun z : β × (Fin n → β) =>
                  ENNReal.ofReal (f (Fin.last n) z.1) *
                    ENNReal.ofReal
                      (∏ i : Fin n, f i.castSucc (z.2 i))) := by
            funext z
            rw [ENNReal.ofReal_mul]
            exact hf_nonneg (Fin.last n) z.1
          have hmeas_prod : Measurable
              (fun z : Fin n → β => ∏ i : Fin n, f i.castSucc (z i)) := by
            fun_prop
          rw [hmul]
          rw [MeasureTheory.prod_withDensity
            (μ := ν)
            (ν := MeasureTheory.Measure.pi (fun _ : Fin n => ν))
            (f := fun a => ENNReal.ofReal (f (Fin.last n) a))
            (g := fun z : Fin n → β =>
              ENNReal.ofReal (∏ i : Fin n, f i.castSucc (z i)))
            (by simpa using (hf_meas (Fin.last n)).ennreal_ofReal)
            (by simpa using hmeas_prod.ennreal_ofReal)]
        _ = (densityMeasure ν (f (Fin.last n))).prod
            (MeasureTheory.Measure.pi
              (fun i : Fin n => densityMeasure ν (f i.castSucc))) := by
          rw [ih (fun i => f i.castSucc) (fun i => hf_meas i.castSucc)
            (fun i x => hf_nonneg i.castSucc x)]
        _ = MeasureTheory.Measure.map e
            (MeasureTheory.Measure.pi
              (fun i : Fin (n + 1) => densityMeasure ν (f i))) := by
          haveI : ∀ i : Fin (n + 1),
              MeasureTheory.SigmaFinite (densityMeasure ν (f i)) := by
            intro i
            unfold densityMeasure
            infer_instance
          symm
          simpa [e] using
            (MeasureTheory.measurePreserving_piFinSuccAbove
              (μ := fun i : Fin (n + 1) => densityMeasure ν (f i))
              (i := Fin.last n)).map_eq

end

end Mf.DP
