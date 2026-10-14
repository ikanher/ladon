import Main

#check surveyDisjunction
#check recordedChoice
#check result

theorem original_inference_not_valid :
    ¬ (∀ (blue tea coffee : Prop), blue → (blue → tea ∨ coffee) → tea → coffee) := by
  intro h
  have falseCoffee : False := h True True False True (fun _ => Or.inl trivial) True
  exact falseCoffee
