import NavierStokes.SmoothFamilyTorusInverse

noncomputable section
open Set
open scoped ContDiff
namespace LadonSourcePair
open NavierStokes.TorusInverse
open NavierStokes.SmoothFamilyTorusInverse

abbrev NoParameter := Fin 0 → ℝ

/-- Remove a zero-dimensional dummy parameter; no slow derivatives remain. -/
def eraseParameter : (NoParameter × Plane) ≃ₗᵢ[ℝ] Plane where
  toLinearEquiv := (LinearEquiv.prodComm ℝ NoParameter Plane).trans LinearEquiv.prodUnique
  norm_map' := by
    intro z
    change ‖z.2‖ = max ‖z.1‖ ‖z.2‖
    have hz : z.1 = 0 := Subsingleton.elim _ _
    simp [hz]

def liftSource (F : Plane → ℂ) : Source NoParameter := F ∘ eraseParameter

/-- A chosen full-Frechet norm convention, NOT a definition extracted from the paper. -/
def TorusJetBound (F : Plane → ℂ) (n : ℕ) (C : ℝ) : Prop :=
  ∀ j ≤ n, ∀ Y, ‖iteratedFDeriv ℝ j F Y‖ ≤ C

theorem norm_liftSource (F : Plane → ℂ) (p : NoParameter) (Y : Plane) (j : ℕ) :
    ‖iteratedFDeriv ℝ j (liftSource F) (p, Y)‖ = ‖iteratedFDeriv ℝ j F Y‖ := by
  exact eraseParameter.norm_iteratedFDeriv_comp_right F (p, Y) j

theorem bound_equiv (F : Plane → ℂ) (n : ℕ) (C : ℝ) :
    JetBound (liftSource F) Set.univ n C ↔ TorusJetBound F n C := by
  constructor
  · intro h j hj Y
    rw [← norm_liftSource F 0 Y j]
    exact h j hj 0 (Set.mem_univ _) Y
  · intro h j hj p _ Y
    rw [norm_liftSource]
    exact h j hj Y

def planeInverse (d : Direction) (F : Plane → ℂ) : Plane → ℂ :=
  directionalInverse d (NavierStokes.SmoothFourierData.coefficient F)

theorem lift_inverse (d : Direction) (F : Plane → ℂ) :
    inverse d (liftSource F) = liftSource (planeInverse d F) := by
  rfl

/-- Specialization of the existing five-order theorem; no four-order estimate asserted. -/
theorem plane_inverse_five (d : Direction) (n : ℕ) :
    ∃ K : ℝ, 0 ≤ K ∧ ∀ (F : Plane → ℂ) (C : ℝ),
      ContDiff ℝ ∞ F → NavierStokes.SmoothFourierData.UnitPeriodic F → 0 ≤ C →
      TorusJetBound F (n + 5) C → TorusJetBound (planeInverse d F) n (K * C) := by
  obtain ⟨K, hK, h⟩ := inverse_finiteJets (P := NoParameter) d n
  refine ⟨K, hK, ?_⟩
  intro F C hf hp hC hbound
  have hs : ContDiff ℝ ∞ (liftSource F) :=
    hf.comp eraseParameter.toContinuousLinearEquiv.contDiff
  have hper : Periodic (liftSource F) := fun _ => hp
  have hinput := (bound_equiv F (n + 5) C).mpr hbound
  have houtput := h (liftSource F) Set.univ C hs hper hC hinput
  rw [lift_inverse] at houtput
  exact (bound_equiv (planeInverse d F) n (K * C)).mp houtput

#print axioms bound_equiv
#print axioms plane_inverse_five
end LadonSourcePair
