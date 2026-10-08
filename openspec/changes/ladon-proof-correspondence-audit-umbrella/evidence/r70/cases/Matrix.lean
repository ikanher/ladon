import Mathlib.Analysis.Matrix.Spectrum
import Mathlib.LinearAlgebra.Matrix.Trace
import Mathlib.Tactic
namespace Audit.MatrixCase
open Matrix
open scoped BigOperators Matrix
variable {n : Type*} [Fintype n] [DecidableEq n]

-- Valid alternative: no eigenbasis or change of basis.
theorem direct (A : Matrix n n ℝ) (hA : Aᵀ = A) : 0 ≤ trace (A*A) := by
  unfold trace
  simp only [diag, mul_apply]
  apply Finset.sum_nonneg
  intro i hi
  apply Finset.sum_nonneg
  intro j hj
  have hij : A j i = A i j := by
    simpa only [transpose_apply] using congrFun (congrFun hA i) j
  rw [hij]
  exact mul_self_nonneg _

-- Faithful control: spectral decomposition, trace invariance, diagonal squares.
theorem diagonalization (A : Matrix n n ℝ) (hA : Aᵀ = A) :
    0 ≤ trace (A*A) := by
  have hH : A.IsHermitian := (isHermitian_iff_isSymm).mpr hA
  let U := hH.eigenvectorUnitary
  let D : Matrix n n ℝ := diagonal hH.eigenvalues
  have hdiag : A = Unitary.conjStarAlgAut ℝ _ U D := by
    simpa [U, D] using hH.spectral_theorem
  have hsquare : A*A = Unitary.conjStarAlgAut ℝ _ U (D*D) := by
    rw [hdiag, map_mul]
  have htrace : trace (A*A) = trace (D*D) := by
    rw [hsquare, Unitary.conjStarAlgAut_apply, trace_mul_cycle,
      Unitary.coe_star_mul_self, one_mul]
  rw [htrace]
  simp only [D, diagonal_mul_diagonal, trace_diagonal]
  exact Finset.sum_nonneg (fun i hi => mul_self_nonneg _)

#print axioms direct
#print axioms diagonalization
end Audit.MatrixCase
