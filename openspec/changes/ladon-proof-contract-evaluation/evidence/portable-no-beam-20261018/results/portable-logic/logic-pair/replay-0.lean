import Lean
import EvalLogic
set_option autoImplicit false
theorem ladonEvaluationReplay (P : Prop) (Q : Prop) (hP : P) (hQ : Q) : P ∧ Q := by
  intros
  apply EvalLogic.pair
  all_goals assumption
#print axioms ladonEvaluationReplay
