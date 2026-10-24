import Lean
namespace EvalLogic
theorem keep {P : Prop} (h : P) : P := h
theorem pair {P Q : Prop} (hP : P) (hQ : Q) : P ∧ Q := ⟨hP, hQ⟩
theorem flip {P Q : Prop} (h : P ∧ Q) : Q ∧ P := ⟨h.2, h.1⟩
end EvalLogic
