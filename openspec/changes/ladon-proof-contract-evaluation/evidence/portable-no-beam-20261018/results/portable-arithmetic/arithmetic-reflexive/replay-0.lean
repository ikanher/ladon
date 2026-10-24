import Lean
import EvalArithmetic
set_option autoImplicit false
theorem ladonEvaluationReplay (n : Nat) : n = n := by
  intros
  apply EvalArithmetic.reflexive
  all_goals assumption
#print axioms ladonEvaluationReplay
