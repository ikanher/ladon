import Lean

theorem surveyDisjunction (blue tea coffee : Prop) (hBlue : blue) (hRule : blue → (tea ∨ coffee)) : tea ∨ coffee := by
  exact hRule hBlue

theorem recordedChoice (coffee : Prop) (hRecord : coffee) : coffee := by
  exact hRecord

theorem result (blue tea coffee : Prop) (hBlue : blue) (hRule : blue → (tea ∨ coffee)) (hTea : tea) (hCoffee : coffee) : coffee := by
  have _hSurvey := surveyDisjunction blue tea coffee hBlue hRule
  exact recordedChoice coffee hCoffee
