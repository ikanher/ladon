import Mf.DP.EuclideanVectorClippingRegularity
import Mathlib.MeasureTheory.Constructions.Pi
import Mathlib.MeasureTheory.Integral.Prod
import Mathlib.Data.Fin.Tuple.Basic

/-!
# Finite independent histories and the actual update recursion

The history law is a finite product of a mask/noise product law. Newest samples
sit at the head, so the preceding iterate uses the independent tail. The update
is x - eta (h + z), with no boundedness assumption on noise. Bounded clipped
drift and square-integrable noise give finite moments of every finite iterate.
-/

namespace Mf.Optimization.PoissonClippedSGD.Trajectory
open MeasureTheory
noncomputable section

variable {d : ℕ} {Mask : Type*} [MeasurableSpace Mask]

abbrev V (d : ℕ) := EuclideanSpace ℝ (Fin d)
abbrev Step (d : ℕ) (Mask : Type*) := Mask × V d
abbrev History (d : ℕ) (Mask : Type*) (T : ℕ) := Fin T → Step d Mask
def historyLaw (ν : Measure (Step d Mask)) (T : ℕ) : Measure (History d Mask T) :=
  Measure.pi (fun _ : Fin T => ν)
def update (η : ℝ) (h : V d → Mask → V d)
    (x : V d) (sample : Step d Mask) : V d :=
  x - η • (h x sample.1 + sample.2)

def run (η : ℝ) (h : V d → Mask → V d) (x₀ : V d) :
    (T : ℕ) → History d Mask T → V d
  | 0, _ => x₀
  | T + 1, ω => update η h (run η h x₀ T (Fin.tail ω)) (ω 0)

theorem history_split (ν : Measure (Step d Mask))
    [IsProbabilityMeasure ν] (T : ℕ) :
    MeasurePreserving (fun ω : History d Mask (T + 1) => (ω 0, Fin.tail ω))
      (historyLaw ν (T + 1)) (ν.prod (historyLaw ν T)) := by
  have hp := MeasureTheory.measurePreserving_piFinSuccAbove
    (μ := fun _ : Fin (T + 1) => ν) (i := 0)
  convert hp using 1
  · funext ω
    apply Prod.ext
    · simp [MeasurableEquiv.piFinSuccAbove, Fin.succAbove_zero]
    · funext i
      simp [MeasurableEquiv.piFinSuccAbove, Fin.succAbove_zero]
  · rfl
  · rfl

theorem history_split_measurableEmbedding (T : ℕ) :
    MeasurableEmbedding
      (fun ω : History d Mask (T + 1) => (ω 0, Fin.tail ω)) := by
  let e := MeasurableEquiv.piFinSuccAbove (fun _ : Fin (T + 1) => Step d Mask) 0
  have he : (fun ω : History d Mask (T + 1) => (ω 0, Fin.tail ω)) = e := by
    funext ω
    apply Prod.ext
    · simp [e, MeasurableEquiv.piFinSuccAbove]
    · funext i
      simp [e, MeasurableEquiv.piFinSuccAbove]
  rw [he]
  exact e.measurableEmbedding

theorem run_succ_integral_fubini
    (ν : Measure (Step d Mask)) [IsProbabilityMeasure ν]
    (η : ℝ) (h : V d → Mask → V d) (x₀ : V d) (T : ℕ)
    (Φ : V d → ℝ)
    (hF : Integrable
      (fun p : Step d Mask × History d Mask T =>
        Φ (update η h (run η h x₀ T p.2) p.1))
      (ν.prod (historyLaw ν T))) :
    (∫ ω : History d Mask (T + 1), Φ (run η h x₀ (T + 1) ω)
      ∂historyLaw ν (T + 1)) =
      ∫ past : History d Mask T, ∫ sample : Step d Mask,
        Φ (update η h (run η h x₀ T past) sample) ∂ν ∂historyLaw ν T := by
  let split := fun ω : History d Mask (T + 1) => (ω 0, Fin.tail ω)
  have hsplit := history_split (d := d) (Mask := Mask) ν T
  have heq : (fun ω : History d Mask (T + 1) =>
      Φ (run η h x₀ (T + 1) ω)) = fun ω =>
        Φ (update η h (run η h x₀ T (Fin.tail ω)) (ω 0)) := by
    funext ω
    rfl
  rw [heq]
  calc
    (∫ ω : History d Mask (T + 1),
        Φ (update η h (run η h x₀ T (Fin.tail ω)) (ω 0))
      ∂historyLaw ν (T + 1)) =
      ∫ ω, (fun p : Step d Mask × History d Mask T =>
        Φ (update η h (run η h x₀ T p.2) p.1)) (split ω)
      ∂historyLaw ν (T + 1) := by rfl
    _ = ∫ p : Step d Mask × History d Mask T,
        Φ (update η h (run η h x₀ T p.2) p.1)
      ∂ν.prod (historyLaw ν T) :=
        hsplit.integral_comp (history_split_measurableEmbedding (d := d) (Mask := Mask) T)
          (fun p => Φ (update η h (run η h x₀ T p.2) p.1))
    _ = ∫ past : History d Mask T, ∫ sample : Step d Mask,
        Φ (update η h (run η h x₀ T past) sample) ∂ν ∂historyLaw ν T := by
      haveI : IsProbabilityMeasure (historyLaw ν T) := by
        dsimp [historyLaw]
        infer_instance
      exact MeasureTheory.integral_prod_symm _ hF

theorem update_measurable (η : ℝ)
    (h : V d → Mask → V d)
    (hh : Measurable (fun p : V d × Mask => h p.1 p.2)) :
    Measurable (fun p : V d × Step d Mask => update η h p.1 p.2) := by
  have hh' : Measurable (fun p : V d × Step d Mask => h p.1 p.2.1) :=
    hh.comp (Measurable.prodMk measurable_fst (measurable_fst.comp measurable_snd))
  have hn : Measurable (fun p : V d × Step d Mask => p.2.2) :=
    measurable_snd.comp measurable_snd
  have heta : Measurable (fun _ : V d × Step d Mask => η) := measurable_const
  exact measurable_fst.sub (heta.smul (hh'.add hn))

theorem run_measurable (η : ℝ) (h : V d → Mask → V d)
    (x₀ : V d)
    (hh : Measurable (fun p : V d × Mask => h p.1 p.2))
    (T : ℕ) : Measurable (run η h x₀ T) := by
  induction T with
  | zero => exact measurable_const
  | succ T ih =>
    have htail : Measurable (Fin.tail : History d Mask (T + 1) →
        History d Mask T) :=
      measurable_pi_lambda _ fun i => measurable_pi_apply i.succ
    have hstate : Measurable (fun ω : History d Mask (T + 1) =>
        run η h x₀ T (Fin.tail ω)) := ih.comp htail
    have hsample : Measurable (fun ω : History d Mask (T + 1) => ω 0) :=
      measurable_pi_apply 0
    change Measurable (fun ω : History d Mask (T + 1) =>
      update η h (run η h x₀ T (Fin.tail ω)) (ω 0))
    exact (update_measurable η h hh).comp (hstate.prodMk hsample)

def noiseNormSum (T : ℕ) (ω : History d Mask T) : ℝ :=
  ∑ i : Fin T, ‖(ω i).2‖

def suffixHistory {T t : ℕ} (ht : t ≤ T) (ω : History d Mask T) : History d Mask t :=
  fun i => ω ⟨T - t + i.val, by omega⟩

def suffixIndexEquiv (T t : ℕ) (ht : t ≤ T) :
    Fin t ≃ {i : Fin T // ¬ i.val < T - t} where
  toFun j := by
    have hsub : T - t + t = T := Nat.sub_add_cancel ht
    have hj : j.val < t := j.isLt
    have hval : T - t + j.val < T := by omega
    have hnot : ¬ T - t + j.val < T - t := by omega
    exact ⟨⟨T - t + j.val, hval⟩, hnot⟩
  invFun i := ⟨i.val - (T - t), by omega⟩
  left_inv j := by
    apply Fin.ext
    simp [Nat.add_sub_cancel_left]
  right_inv i := by
    apply Subtype.ext
    apply Fin.ext
    have hge : T - t ≤ i.1.val := Nat.le_of_not_gt i.2
    simp only [Fin.val_mk]
    omega

theorem suffixHistory_measurePreserving
    (ν : Measure (Step d Mask)) [IsProbabilityMeasure ν]
    {T t : ℕ} (ht : t ≤ T) :
    MeasurePreserving (suffixHistory (d := d) (Mask := Mask) ht)
      (historyLaw ν T) (historyLaw ν t) := by
  classical
  let p : Fin T → Prop := fun i => i.val < T - t
  let e := MeasurableEquiv.piEquivPiSubtypeProd
    (fun _ : Fin T => Step d Mask) p
  let eidx := suffixIndexEquiv T t ht
  let r := MeasurableEquiv.piCongrLeft
    (fun _ : {j : Fin T // ¬ p j} => Step d Mask) eidx
  have hp := MeasureTheory.measurePreserving_piEquivPiSubtypeProd
    (μ := fun _ : Fin T => ν) p
  haveI : IsProbabilityMeasure (Measure.pi (fun i : {j : Fin T // p j} => ν)) := inferInstance
  have hsnd := MeasureTheory.measurePreserving_snd
    (μ := Measure.pi (fun i : {j : Fin T // p j} => ν))
    (ν := Measure.pi (fun i : {j : Fin T // ¬ p j} => ν))
  have hreindex := MeasureTheory.measurePreserving_piCongrLeft
    (α := fun _ : {j : Fin T // ¬ p j} => Step d Mask)
    (μ := fun _ : {j : Fin T // ¬ p j} => ν) eidx
  have hcomp : MeasurePreserving ((r.symm ∘ Prod.snd) ∘ e)
      (historyLaw ν T) (historyLaw ν t) := by
    simpa only [historyLaw, r, e] using (hreindex.symm.comp hsnd).comp hp
  have hfun : ((r.symm ∘ Prod.snd) ∘ e) =
      suffixHistory ht := by
    funext ω
    funext i
    simp [e, eidx, r, p, suffixHistory, MeasurableEquiv.piEquivPiSubtypeProd,
      Equiv.piEquivPiSubtypeProd, MeasurableEquiv.piCongrLeft,
      Equiv.piCongrLeft, suffixIndexEquiv]
  simpa only [hfun] using hcomp

theorem suffixHistory_succ {T t : ℕ} (ht : t + 1 ≤ T)
    (ω : History d Mask T) :
    suffixHistory ht ω = Fin.cons
      (ω ⟨T - 1 - t, by omega⟩)
      (suffixHistory (Nat.le_trans (Nat.le_succ t) ht) ω) := by
  funext i
  refine Fin.cases ?_ (fun j => ?_) i
  · change ω ⟨T - (t + 1) + 0, by omega⟩ = ω ⟨T - 1 - t, by omega⟩
    apply congrArg ω
    apply Fin.ext
    simp
    omega
  · change ω ⟨T - (t + 1) + j.succ.val, by omega⟩ =
      ω ⟨T - t + j.val, by omega⟩
    apply congrArg ω
    apply Fin.ext
    simp
    omega

def iterateOnHistory (η : ℝ) (h : V d → Mask → V d) (x₀ : V d)
    (T t : ℕ) (ht : t ≤ T) (ω : History d Mask T) : V d :=
  run η h x₀ t (suffixHistory ht ω)

theorem iterateOnHistory_zero (η : ℝ) (h : V d → Mask → V d) (x₀ : V d)
    (T : ℕ) (ω : History d Mask T) : iterateOnHistory η h x₀ T 0 (Nat.zero_le _) ω = x₀ := by
  simp [iterateOnHistory, run]

theorem iterateOnHistory_succ (η : ℝ) (h : V d → Mask → V d) (x₀ : V d)
    {T t : ℕ} (ht : t + 1 ≤ T) (ω : History d Mask T) :
    iterateOnHistory η h x₀ T (t + 1) ht ω =
      update η h (iterateOnHistory η h x₀ T t (Nat.le_trans (Nat.le_succ t) ht) ω)
        (ω ⟨T - 1 - t, by omega⟩) := by
  unfold iterateOnHistory
  rw [suffixHistory_succ ht ω]
  simp [run]

theorem iterateOnHistory_full (η : ℝ) (h : V d → Mask → V d) (x₀ : V d)
    (T : ℕ) (ω : History d Mask T) :
    iterateOnHistory η h x₀ T T (Nat.le_refl T) ω = run η h x₀ T ω := by
  unfold iterateOnHistory
  have heq : suffixHistory (Nat.le_refl T) ω = ω := by
    funext i
    simp [suffixHistory]
  rw [heq]

theorem iterateOnHistory_integral_eq
    (ν : Measure (Step d Mask)) [IsProbabilityMeasure ν]
    (η : ℝ) (h : V d → Mask → V d) (x₀ : V d)
    {T t : ℕ} (ht : t ≤ T) (Φ : V d → ℝ)
    (hΦ : Integrable (fun ω : History d Mask t => Φ (run η h x₀ t ω))
      (historyLaw ν t)) :
    (∫ ω : History d Mask T, Φ (iterateOnHistory η h x₀ T t ht ω)
      ∂historyLaw ν T) =
    (∫ ω : History d Mask t, Φ (run η h x₀ t ω) ∂historyLaw ν t) := by
  let p : History d Mask T → History d Mask t :=
    suffixHistory (d := d) (Mask := Mask) ht
  have hmp := suffixHistory_measurePreserving (d := d) (Mask := Mask) ν ht
  have hFmap : AEStronglyMeasurable (fun ω : History d Mask t => Φ (run η h x₀ t ω))
      (Measure.map p (historyLaw ν T)) := by
    rw [hmp.map_eq]
    exact hΦ.aestronglyMeasurable
  calc
    (∫ ω : History d Mask T, Φ (iterateOnHistory η h x₀ T t ht ω)
        ∂historyLaw ν T) =
      ∫ ω, Φ (run η h x₀ t (p ω)) ∂historyLaw ν T := by rfl
    _ = ∫ ω : History d Mask t, Φ (run η h x₀ t ω)
        ∂Measure.map p (historyLaw ν T) := by
          symm
          exact MeasureTheory.integral_map hmp.measurable.aemeasurable hFmap
    _ = ∫ ω : History d Mask t, Φ (run η h x₀ t ω) ∂historyLaw ν t := by
          rw [hmp.map_eq]

theorem history_noiseNormSum_memLp
    (maskLaw : Measure Mask) (noiseLaw : Measure (V d))
    [IsProbabilityMeasure maskLaw] [IsProbabilityMeasure noiseLaw]
    (hnoise : MemLp (fun z : V d => ‖z‖) 2 noiseLaw) (T : ℕ) :
    MemLp (noiseNormSum (d := d) (Mask := Mask) T)
      2 (historyLaw (maskLaw.prod noiseLaw) T) := by
  classical
  let ν : Measure (Step d Mask) := maskLaw.prod noiseLaw
  let μ := historyLaw ν T
  have hstep : MemLp (fun sample : Step d Mask => ‖sample.2‖) 2 ν := by
    exact hnoise.comp_measurePreserving (MeasureTheory.measurePreserving_snd)
  have hcoord (i : Fin T) : MemLp (fun ω : History d Mask T => ‖(ω i).2‖) 2 μ := by
    have hp := MeasureTheory.measurePreserving_eval (fun _ : Fin T => ν) i
    exact hstep.comp_measurePreserving hp
  have hsum (s : Finset (Fin T)) :
      MemLp (fun ω : History d Mask T => s.sum fun i => ‖(ω i).2‖) 2 μ := by
    induction s using Finset.induction_on with
    | empty => simpa using (MeasureTheory.memLp_const (μ := μ) (0 : ℝ))
    | @insert i s his ih =>
      have hsumEq : (fun ω : History d Mask T => ∑ j ∈ insert i s, ‖(ω j).2‖) =
          (fun ω => ‖(ω i).2‖ + ∑ j ∈ s, ‖(ω j).2‖) := by
        funext ω
        simp [Finset.sum_insert, his]
      rw [hsumEq]
      exact (hcoord i).add ih
  change MemLp (fun ω : History d Mask T => ∑ i : Fin T, ‖(ω i).2‖) 2
    (historyLaw (maskLaw.prod noiseLaw) T)
  simpa [noiseNormSum] using hsum Finset.univ

theorem update_norm_le (η M : ℝ) (hM : 0 ≤ M)
    (h : V d → Mask → V d) (x : V d) (sample : Step d Mask)
    (hb : ‖h x sample.1‖ ≤ M) :
    ‖update η h x sample‖ ≤ ‖x‖ + |η| * (M + ‖sample.2‖) := by
  have hη : 0 ≤ |η| := abs_nonneg _
  have hnoise : 0 ≤ ‖sample.2‖ := norm_nonneg _
  calc
    ‖update η h x sample‖ ≤ ‖x‖ + ‖η • (h x sample.1 + sample.2)‖ := norm_sub_le _ _
    _ = ‖x‖ + |η| * ‖h x sample.1 + sample.2‖ := by
      rw [norm_smul, Real.norm_eq_abs]
    _ ≤ ‖x‖ + |η| * (‖h x sample.1‖ + ‖sample.2‖) := by
      gcongr
      exact norm_add_le _ _
    _ ≤ ‖x‖ + |η| * (M + ‖sample.2‖) := by gcongr

theorem run_norm_le (η M : ℝ) (hM : 0 ≤ M)
    (h : V d → Mask → V d) (x₀ : V d) (T : ℕ)
    (hb : ∀ x m, ‖h x m‖ ≤ M) (ω : History d Mask T) :
    ‖run η h x₀ T ω‖ ≤ ‖x₀‖ + |η| * ((T : ℝ) * M + noiseNormSum T ω) := by
  induction T with
  | zero => simp [run, noiseNormSum]
  | succ T ih =>
    rw [run]
    have hstep := update_norm_le η M hM h (run η h x₀ T (Fin.tail ω)) (ω 0)
      (hb _ _)
    have htail := ih (Fin.tail ω)
    have hnoiseEq : noiseNormSum (T + 1) ω = ‖(ω 0).2‖ + noiseNormSum T (Fin.tail ω) := by
      simp [noiseNormSum, Fin.sum_univ_succ]
      change (∑ i : Fin T, ‖(ω i.succ).2‖) =
        ∑ i : Fin T, ‖(Fin.tail ω i).2‖
      rfl
    rw [hnoiseEq]
    push_cast
    calc
      ‖update η h (run η h x₀ T (Fin.tail ω)) (ω 0)‖ ≤
          ‖run η h x₀ T (Fin.tail ω)‖ + |η| * (M + ‖(ω 0).2‖) := hstep
      _ ≤ ‖x₀‖ + |η| * ((T : ℝ) * M + noiseNormSum T (Fin.tail ω)) +
          |η| * (M + ‖(ω 0).2‖) := by linarith
      _ = ‖x₀‖ + |η| * ((↑T + 1) * M +
          (‖(ω 0).2‖ + noiseNormSum T (Fin.tail ω))) := by ring

theorem run_normSq_integrable
    (maskLaw : Measure Mask) (noiseLaw : Measure (V d))
    [IsProbabilityMeasure maskLaw] [IsProbabilityMeasure noiseLaw]
    (η M : ℝ) (hM : 0 ≤ M)
    (h : V d → Mask → V d) (x₀ : V d)
    (hh : Measurable (fun p : V d × Mask => h p.1 p.2))
    (hb : ∀ x m, ‖h x m‖ ≤ M)
    (hnoise : MemLp (fun z : V d => ‖z‖) 2 noiseLaw) (T : ℕ) :
    Integrable (run η h x₀ T) (historyLaw (maskLaw.prod noiseLaw) T) ∧
    Integrable (fun ω : History d Mask T => ‖run η h x₀ T ω‖ ^ 2)
      (historyLaw (maskLaw.prod noiseLaw) T) := by
  let ν : Measure (Step d Mask) := maskLaw.prod noiseLaw
  let μ := historyLaw ν T
  haveI : IsProbabilityMeasure ν := inferInstance
  haveI : IsProbabilityMeasure μ := by dsimp [μ, historyLaw]; infer_instance
  have hsum := history_noiseNormSum_memLp (d := d) (Mask := Mask)
    maskLaw noiseLaw hnoise T
  have hconstant : MemLp (fun _ : History d Mask T => (T : ℝ) * M) 2 μ :=
    MeasureTheory.memLp_const _
  have hinside := hconstant.add hsum
  have hscaled := hinside.const_mul |η|
  have hbound : MemLp (fun ω : History d Mask T => ‖x₀‖ + |η| *
      ((T : ℝ) * M + noiseNormSum T ω)) 2 μ := by
    have hc : MemLp (fun _ : History d Mask T => ‖x₀‖) 2 μ := MeasureTheory.memLp_const _
    exact hc.add hscaled
  have hrun : MemLp (run η h x₀ T) 2 μ := by
    apply hbound.mono' (run_measurable η h x₀ hh T).aestronglyMeasurable
    filter_upwards [] with ω
    simpa using run_norm_le η M hM h x₀ T hb ω
  exact ⟨hrun.integrable (by norm_num), hrun.integrable_norm_pow (by norm_num)⟩

end
end Mf.Optimization.PoissonClippedSGD.Trajectory
