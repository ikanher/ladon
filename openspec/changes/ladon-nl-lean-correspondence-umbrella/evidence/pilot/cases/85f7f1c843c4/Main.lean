import Lean

theorem localRetention (isLocal retained : Prop) (hLocal : isLocal) (hRule : isLocal → retained) : retained := by
  exact hRule hLocal

theorem inventoryRecordCode (codeSeven : Prop) (hInventory : codeSeven) : codeSeven := by
  exact hInventory

theorem result (nearby retained codeSeven : Prop) (hNearby : nearby) (hRule : nearby → retained) (hIndependent : codeSeven) : codeSeven := by
  have _hRetained := localRetention nearby retained hNearby hRule
  exact inventoryRecordCode codeSeven hIndependent
