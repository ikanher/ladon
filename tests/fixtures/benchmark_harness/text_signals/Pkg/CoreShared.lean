/- axiom BlockFake : True -/
def quoted : String := "constant StringFake : Nat"
-- opaque LineFake : Nat
@[simp] private theorem keptTheorem : True := by trivial
noncomputable def keptDef : Nat := 1
unsafe def keptUnsafe : Nat := 2
opaque keptOpaque : Nat
axiom keptAxiom : True
constant keptConstant : Nat
theorem trustedMarker : True := by
  sorry
