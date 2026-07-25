import Init

namespace LadonDeclarationFixture

scoped notation "importedZero" => Nat.zero

def importedDependency : Nat := Nat.succ Nat.zero

axiom importedAxiom : True

end LadonDeclarationFixture
