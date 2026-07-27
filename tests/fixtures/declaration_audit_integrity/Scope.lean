namespace Fixture

section Parameters

/- namespace Commented -/
def stringCarrier : String := "theorem StringOnly : True"

@[simp] protected theorem visibleResult : True := by
  trivial

private def hiddenResult : Nat := 1

local instance localResult : Inhabited Nat where
  default := 0

namespace Nested

noncomputable def qualifiedResult : Nat := 2

end Nested
end Parameters
end Fixture

namespace Fixture

mutual
  def mutualLeft : Nat := mutualRight
  def mutualRight : Nat := 0
end

def recovered : Nat := 3

end Fixture
