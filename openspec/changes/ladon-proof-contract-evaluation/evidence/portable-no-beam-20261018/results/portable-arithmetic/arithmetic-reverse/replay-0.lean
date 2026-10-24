import Lean
import EvalArithmetic
set_option autoImplicit false
theorem ladonEvaluationReplay (m : Nat) (n : Nat) (h : m = n) : n = m := by
  intros
  apply EvalArithmetic.reverse
  all_goals assumption
#print axioms ladonEvaluationReplay
