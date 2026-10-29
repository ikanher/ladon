-- Appended to TransferExamples.lean by the live qualification harness.
namespace MatrixExamples
def ident (f : Real) := f
theorem setLeft (S T : Set Nat) (n : Nat) : ∃ K : Real, 0 ≤ K ∧ ∀ f C, 0 ≤ C →
    TransferExamples.bound f S n C → TransferExamples.bound (ident f) S n (K*C) := by
  refine ⟨1, zero_le_one, ?_⟩
  intro f C _ h
  simpa only [one_mul, ident] using h
theorem setRight (S T : Set Nat) (n : Nat) : ∃ K : Real, 0 ≤ K ∧ ∀ f C, 0 ≤ C →
    TransferExamples.bound f T n C → TransferExamples.bound (ident f) T n (K*C) := by
  refine ⟨1, zero_le_one, ?_⟩
  intro f C _ h
  simpa only [one_mul, ident] using h
def identF (f : Nat → Real) := f
theorem paramLeft (a b : Real) (n : Nat) : ∃ K : Real, 0 ≤ K ∧ ∀ f S C, 0 ≤ C →
    TransferExamples.Functions.bound a f S n C →
    TransferExamples.Functions.bound a (identF f) S n (K*C) := by
  refine ⟨1, zero_le_one, ?_⟩
  intro f S C _ h
  simpa only [one_mul, identF] using h
theorem paramRight (a b : Real) (n : Nat) : ∃ K : Real, 0 ≤ K ∧ ∀ f S C, 0 ≤ C →
    TransferExamples.Functions.bound b f S n C →
    TransferExamples.Functions.bound b (identF f) S n (K*C) := by
  refine ⟨1, zero_le_one, ?_⟩
  intro f S C _ h
  simpa only [one_mul, identF] using h
theorem pointwise (f : Real) (n : Nat) : ∃ K : Real, 0 ≤ K ∧ ∀ S C, 0 ≤ C →
    TransferExamples.bound f S (n+4) C → TransferExamples.bound (TransferExamples.twice f) S n (K*C) := by
  refine ⟨2, by norm_num, ?_⟩
  intro S C _ h j hj p hp y
  exact mul_le_mul_of_nonneg_left (h j (Nat.le_trans hj (Nat.le_add_right n 4)) p hp y) (by norm_num)
theorem endpoint (n : Nat) : ∃ K : Real, 0 ≤ K ∧ ∀ f S C, 0 ≤ C →
    TransferExamples.bound f S (n+4) C → TransferExamples.bound (TransferExamples.thrice f) S n (K*C) := by
  refine ⟨3, by norm_num, ?_⟩
  intro f S C _ h j hj p hp y
  exact mul_le_mul_of_nonneg_left (h j (Nat.le_trans hj (Nat.le_add_right n 4)) p hp y) (by norm_num)
end MatrixExamples
