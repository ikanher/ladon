import Main
#check conditionalApplication
#print conditionalApplication
#check result
#print result
example : ¬ (True → False) := by
  intro h
  exact h trivial
