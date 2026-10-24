import Lean
import EvalLogic
set_option autoImplicit false
theorem ladonEvaluationReplay (P : Prop) (h : P) : P := by
  intros
  apply EvalLogic.keep
  all_goals assumption
#print axioms ladonEvaluationReplay
