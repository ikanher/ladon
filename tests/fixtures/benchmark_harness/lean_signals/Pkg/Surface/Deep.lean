import Pkg.Dep

namespace Pkg

axiom surfaceAxiom : Nat

def helperValue : Nat := dependencyValue

opaque hiddenValue : Nat := 2

unsafe def unsafeValue : Nat := 3

theorem parentValue : True := by trivial

end Pkg

namespace Other.Space

theorem first : True := by trivial

theorem second : True := by trivial

end Other.Space
