import Lean

theorem conditionalApplication (safe quiet : Prop) (hs : safe) (rule : safe → quiet) : quiet := by
  exact rule hs

theorem result (safe quiet : Prop) (hs : safe) (rule : safe → quiet) : quiet := by
  exact conditionalApplication safe quiet hs rule
