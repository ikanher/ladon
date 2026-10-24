import Lean
namespace EvalArithmetic
theorem reflexive (n : Nat) : n = n := rfl
theorem reverse {m n : Nat} (h : m = n) : n = m := h.symm
theorem transitive {m n k : Nat} (h₁ : m = n) (h₂ : n = k) : m = k := h₁.trans h₂
end EvalArithmetic
