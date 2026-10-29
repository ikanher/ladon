import NavierStokes.SmoothFamilyTorusInverse

noncomputable section
open scoped BigOperators ContDiff
namespace LadonCoordinateNorm

-- Generic finite coordinate expansion, independent of any paper or operator.
theorem norm_le_components {E G : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    [NormedAddCommGroup G] [NormedSpace ℝ G] {d n : ℕ}
    (basis : Fin d → E) (coord : E → Fin d → ℝ)
    (expand : ∀ x, ∑ k, coord x k • basis k = x)
    (coord_le : ∀ x k, ‖coord x k‖ ≤ ‖x‖)
    (T : ContinuousMultilinearMap ℝ (fun _ : Fin n => E) G)
    {C : ℝ} (hC : 0 ≤ C) (h : ∀ a : Fin n → Fin d, ‖T (basis ∘ a)‖ ≤ C) :
    ‖T‖ ≤ (d : ℝ)^n * C := by
  apply ContinuousMultilinearMap.opNorm_le_bound (by positivity)
  intro v
  have hv : (fun i => ∑ k, coord (v i) k • basis k) = v := funext fun i => expand (v i)
  conv_lhs => rw [← hv, T.map_sum]
  calc
    ‖∑ a : Fin n → Fin d, T (fun i => coord (v i) (a i) • basis (a i))‖
      ≤ ∑ a : Fin n → Fin d, ‖T (fun i => coord (v i) (a i) • basis (a i))‖ := norm_sum_le _ _
    _ ≤ ∑ _a : Fin n → Fin d, C * ∏ i, ‖v i‖ := by
      apply Finset.sum_le_sum
      intro a _
      rw [T.map_smul_univ, norm_smul, norm_prod]
      calc
        (∏ i, ‖coord (v i) (a i)‖) * ‖T (fun i => basis (a i))‖
          ≤ (∏ i, ‖v i‖) * C := by
            apply mul_le_mul
            · exact Finset.prod_le_prod (fun _ _ => norm_nonneg _) (fun i _ => coord_le (v i) (a i))
            · exact h a
            · exact norm_nonneg _
            · positivity
        _ = C * ∏ i, ‖v i‖ := mul_comm _ _
    _ = (d : ℝ)^n * C * ∏ i, ‖v i‖ := by simp [mul_assoc]

abbrev Plane := ℝ × ℝ

def planeBasis : Fin 2 → Plane := ![(1, 0), (0, 1)]
def planeCoord (x : Plane) : Fin 2 → ℝ := ![x.1, x.2]

theorem plane_expand (x : Plane) : ∑ k, planeCoord x k • planeBasis k = x := by
  ext <;> simp [planeCoord, planeBasis, Fin.sum_univ_two]

theorem plane_coord_le (x : Plane) (k : Fin 2) : ‖planeCoord x k‖ ≤ ‖x‖ := by
  fin_cases k
  · exact le_max_left _ _
  · exact le_max_right _ _

theorem plane_basis_norm (k : Fin 2) : ‖planeBasis k‖ = 1 := by
  fin_cases k <;> norm_num [planeBasis, Prod.norm_def]

def CoordinateBound (F : Plane → ℂ) (n : ℕ) (C : ℝ) : Prop :=
  ∀ j ≤ n, ∀ Y, ∀ a : Fin j → Fin 2,
    ‖iteratedFDeriv ℝ j F Y (planeBasis ∘ a)‖ ≤ C

def FrechetBound (F : Plane → ℂ) (n : ℕ) (C : ℝ) : Prop :=
  ∀ j ≤ n, ∀ Y, ‖iteratedFDeriv ℝ j F Y‖ ≤ C

theorem frechet_to_coordinate {F : Plane → ℂ} {n : ℕ} {C : ℝ}
    (h : FrechetBound F n C) : CoordinateBound F n C := by
  intro j hj Y a
  simpa [Function.comp_def, plane_basis_norm] using
    (ContinuousMultilinearMap.le_of_opNorm_le (h j hj Y) (planeBasis ∘ a))

theorem coordinate_to_frechet {F : Plane → ℂ} {n : ℕ} {C : ℝ}
    (hC : 0 ≤ C) (h : CoordinateBound F n C) : FrechetBound F n (2^n*C) := by
  intro j hj Y
  have hT := norm_le_components planeBasis planeCoord plane_expand plane_coord_le
    (iteratedFDeriv ℝ j F Y) hC (h j hj Y)
  refine hT.trans ?_
  exact mul_le_mul_of_nonneg_right (pow_le_pow_right₀ (by norm_num : (1:ℝ) ≤ 2) hj) hC

-- Repeated directional partials, in an explicitly fixed slot order.
def coordinateWord (F : Plane → ℂ) : (j : ℕ) → (Fin j → Fin 2) → Plane → ℂ
  | 0, _ => F
  | j + 1, a => fun Y => fderiv ℝ (coordinateWord F j (Fin.tail a)) Y (planeBasis (a 0))

theorem coordinateWord_eq {F : Plane → ℂ} (hf : ContDiff ℝ ∞ F)
    (j : ℕ) (a : Fin j → Fin 2) :
    coordinateWord F j a = fun Y => iteratedFDeriv ℝ j F Y (planeBasis ∘ a) := by
  induction j with
  | zero => rfl
  | succ j ih =>
    funext Y
    simp only [coordinateWord, ih]
    symm
    exact DifferentiableAt.iteratedFDeriv_succ_apply_left'
      ((ContDiff.differentiable_iteratedFDeriv (m := j) (by exact_mod_cast (show (j : ℕ∞) < ⊤ from WithTop.coe_lt_top j)) hf) Y)

def WordBound (F : Plane → ℂ) (n : ℕ) (C : ℝ) : Prop :=
  ∀ j ≤ n, ∀ Y, ∀ a : Fin j → Fin 2, ‖coordinateWord F j a Y‖ ≤ C

theorem wordBound_iff {F : Plane → ℂ} (hf : ContDiff ℝ ∞ F) (n : ℕ) (C : ℝ) :
    WordBound F n C ↔ CoordinateBound F n C := by
  simp only [WordBound, CoordinateBound, coordinateWord_eq hf]

-- Order zero is the function value, not a vacuous derivative condition.
theorem coordinate_zero_iff (F : Plane → ℂ) (C : ℝ) :
    CoordinateBound F 0 C ↔ ∀ Y, ‖F Y‖ ≤ C := by
  simp [CoordinateBound]

-- A unit-coordinate bound cannot in general be transported with constant one.
def sumCoordinates : Plane →L[ℝ] ℝ :=
  ContinuousLinearMap.fst ℝ ℝ ℝ + ContinuousLinearMap.snd ℝ ℝ ℝ

theorem factor_one_is_false :
    (∀ k : Fin 2, ‖sumCoordinates (planeBasis k)‖ ≤ 1) ∧
    ¬ ‖sumCoordinates‖ ≤ 1 := by
  constructor
  · intro k
    fin_cases k <;> norm_num [sumCoordinates, planeBasis]
  · intro h
    have ht := sumCoordinates.le_opNorm (1, 1)
    norm_num [sumCoordinates, Prod.norm_def] at ht
    change ‖ContinuousLinearMap.fst ℝ ℝ ℝ + ContinuousLinearMap.snd ℝ ℝ ℝ‖ ≤ 1 at h
    linarith

#print axioms norm_le_components
#print axioms coordinate_to_frechet
#print axioms frechet_to_coordinate
#print axioms wordBound_iff
#print axioms coordinateWord_eq
#print axioms coordinate_zero_iff
#print axioms factor_one_is_false
end LadonCoordinateNorm
