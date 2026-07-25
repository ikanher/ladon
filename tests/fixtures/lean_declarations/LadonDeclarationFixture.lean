import LadonDeclarationFixture.Imported

open scoped LadonDeclarationFixture

namespace LadonDeclarationFixture

theorem theoremKind : True := by
  trivial

def definitionKind : Nat := importedDependency

axiom axiomKind : True

opaque opaqueKind : Nat := Nat.succ Nat.zero

unsafe def unsafeKind (value : Nat) : Nat := value

theorem structuredStatement
    {α : Type}
    [Inhabited α]
    (value : α)
    (premise : True) :
    True := by
  exact premise

def importedNotation : Nat := importedZero

syntax "lexicalGhost" : term
macro_rules
  | `(lexicalGhost) => `(Nat.succ Nat.zero)

def parserElaboratorDisagreement : Nat := lexicalGhost

theorem rootUsesImportedDependency :
    importedDependency = Nat.succ Nat.zero := by
  rfl

theorem directSorry : True := by
  sorry

theorem directAxiomReference : True := by
  exact axiomKind

theorem importedAxiomReference : True := by
  exact importedAxiom

theorem largeProofBody : True := by
  have h00 : True := True.intro
  have h01 : True := h00
  have h02 : True := h01
  have h03 : True := h02
  have h04 : True := h03
  have h05 : True := h04
  have h06 : True := h05
  have h07 : True := h06
  have h08 : True := h07
  have h09 : True := h08
  have h10 : True := h09
  have h11 : True := h10
  have h12 : True := h11
  have h13 : True := h12
  have h14 : True := h13
  have h15 : True := h14
  have h16 : True := h15
  have h17 : True := h16
  have h18 : True := h17
  have h19 : True := h18
  have h20 : True := h19
  have h21 : True := h20
  have h22 : True := h21
  have h23 : True := h22
  have h24 : True := h23
  have h25 : True := h24
  have h26 : True := h25
  have h27 : True := h26
  have h28 : True := h27
  have h29 : True := h28
  have h30 : True := h29
  have h31 : True := h30
  have h32 : True := h31
  have h33 : True := h32
  have h34 : True := h33
  have h35 : True := h34
  have h36 : True := h35
  have h37 : True := h36
  have h38 : True := h37
  have h39 : True := h38
  have h40 : True := h39
  have h41 : True := h40
  have h42 : True := h41
  have h43 : True := h42
  have h44 : True := h43
  have h45 : True := h44
  have h46 : True := h45
  have h47 : True := h46
  have h48 : True := h47
  have h49 : True := h48
  exact h49

#check LadonDeclarationFixture.theoremKind
#print axioms LadonDeclarationFixture.directAxiomReference

end LadonDeclarationFixture
