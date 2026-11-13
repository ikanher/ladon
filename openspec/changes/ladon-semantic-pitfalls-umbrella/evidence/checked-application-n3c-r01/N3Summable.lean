import Mathlib.Analysis.Normed.Module.FiniteDimension
example (f : ℕ → ℝ) : Summable (fun n => |f n|) ↔ Summable f := by
  simpa only [Real.norm_eq_abs] using (summable_norm_iff (f := f))
