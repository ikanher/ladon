import Main

example : ∃ (isLocal retained codeSeven : Prop),
    isLocal ∧ (isLocal → retained) ∧ ¬ codeSeven :=
  ⟨True, True, False, trivial, (fun _ => trivial), fun h => h⟩

example (codeSeven : Prop) (hInventory : codeSeven) : codeSeven := hInventory
