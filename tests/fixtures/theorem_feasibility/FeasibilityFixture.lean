theorem silly_theorem (n : Nat)
    (h1 : n = 0) (h2 : n = 1) : 2 + 2 = 5 := by
  have h : (0 : Nat) = 1 := h1.symm.trans h2
  have impossible : False := Nat.zero_ne_one h
  exact False.elim impossible

structure BadStructure where
  contradiction : False

theorem prove_anything (P : Prop) (h : BadStructure) : P := by
  exact False.elim h.contradiction

#print axioms prove_anything

theorem inhabitedNat (n : Nat) (_h : n = 0) : True := True.intro
theorem trivialConclusion (n : Nat) (_h1 : n = 0) (_h2 : n = 1) : True := True.intro
theorem propParameter (P : Prop) (h : P) : P := h

structure Renamed where
  impossibleField : False

theorem renamedField (_h : Renamed) : True := True.intro
theorem badStructureTrivial (_P : Prop) (_h : BadStructure) : True := True.intro

structure Decoy where
  contradiction : False → True

example : Decoy := ⟨fun _ => True.intro⟩

theorem legitimateContradiction (_h : Decoy) : True := by
  apply Classical.byContradiction
  intro h
  exact h True.intro

theorem proofDependent (h : False) (_n : (let leaked : Nat := False.elim h; Nat)) :
    True := True.intro

theorem negFalse : ¬ False := fun h => h
theorem explicitArrow : False → False := fun h => h

theorem viaReviewed (h : BadStructure) : False := prove_anything False h

theorem circularRefutation : ¬ (∃ _ : Prop, BadStructure) := by
  intro hex
  obtain ⟨_, h⟩ := hex
  exact viaReviewed h

axiom uncheckedRefutation : ¬ (∃ _ : Prop, BadStructure)

def ordinaryDefinition : Nat := 0

theorem wrongRefutation : ¬ False := fun h => h
theorem «unicode.name» (_h : False) : True := True.intro

theorem independentRefutation : ¬ (∃ _ : Prop, BadStructure) := by
  intro hex
  obtain ⟨_, h⟩ := hex
  exact h.contradiction

theorem LadonFeasibility.certificate : True := True.intro

theorem complementary (P : Prop) (_ : P) (_ : ¬ P) : True := True.intro
theorem complementaryReversed (P : Prop) (_ : ¬ P) (_ : P) : True := True.intro

theorem implicationChain (P Q : Prop) (_ : P) (_ : P → Q) (_ : ¬ Q) : True :=
  True.intro

theorem implicationChainReversed (P Q : Prop) (_ : ¬ Q) (_ : P → Q) (_ : P) : True :=
  True.intro

theorem implicationNearMiss (P Q : Prop) (_ : P → Q) (_ : ¬ Q) : True :=
  True.intro

theorem boolParam (_b : Bool) (_ : False) : True := True.intro

theorem dependentParam (α : Type) (_x : α) (_ : False) : True := True.intro

theorem polymorphicParam (α : Sort u) (_x : α) (_ : False) : True := True.intro

theorem intContradiction (z : Int) (_ : z < 0) (_ : 0 ≤ z) : True := True.intro
theorem intInterval (z : Int) (_ : -2 ≤ z) (_ : z < 0) : True := True.intro

theorem natCycle (a b c : Nat) (_ : a < b) (_ : b ≤ c) (_ : c ≤ a) : True :=
  True.intro

theorem parityGap (a b : Nat) (_ : 2 * a = 2 * b + 1) : True := True.intro

structure NestedBad : Prop where
  inner : BadStructure

theorem nestedProjection (_h : NestedBad) : True := True.intro

structure DataBox : Type where
  evidence : False

theorem dataProjection (_h : DataBox) : True := True.intro

structure TruthField : Prop where
  evidence : True

structure NestedGood : Prop where
  inner : TruthField

theorem nestedInhabited (_h : NestedGood) : True := True.intro

structure IncompatibleBounds (n : Nat) : Prop where
  small : n < 2
  big : n > 5

theorem projectedContradiction (n : Nat) (_h : IncompatibleBounds n) : True :=
  True.intro

structure CompatibleBounds (n : Nat) : Prop where
  small : n < 2
  big : n > 0

theorem projectedInterval (n : Nat) (_h : CompatibleBounds n) : True :=
  True.intro

theorem projectedAfterApply (P : Prop) (hp : P) (f : P → NestedBad) : False :=
  (f hp).inner.contradiction

theorem conjunctionAfterApply (P Q : Prop) (hp : P) (f : P → Q ∧ ¬ Q) : False :=
  (f hp).2 (f hp).1

theorem arithmeticBeforeApply (n : Nat) (_ : n = 0) (f : n < 1 → False) : False :=
  f (by omega)

theorem projectedArithmeticBeforeApply (n : Nat) (h : CompatibleBounds n)
    (f : n = 1 → False) : False :=
  f (by have := h.small; have := h.big; omega)

theorem trueAntecedent (h : True → False) : False := h True.intro

theorem emptyWitness (x : Empty) : False := nomatch x

theorem disjunctionExhausted (P Q : Prop) (h : P ∨ Q) (np : ¬ P) (nq : ¬ Q) : False :=
  h.elim np nq

theorem equalityTransport (α : Type) (P : α → Prop) (x y : α) (eq : x = y)
    (px : P x) (ny : ¬ P y) : False := ny (eq ▸ px)

theorem disjunctionFeasible (P Q : Prop) (_ : P ∨ Q) (_ : ¬ Q) : True := True.intro

theorem projectedArithmeticFeasible (n : Nat) (_ : CompatibleBounds n)
    (_ : n = 0 → False) : True := True.intro

theorem arithmeticProducesWrapper (n : Nat) (_ : n = 0)
    (f : n < 1 → NestedBad) : False :=
  (f (by omega)).inner.contradiction

theorem branchesProduceWrapper (P Q : Prop) (h : P ∨ Q)
    (f : P → NestedBad) (g : Q → NestedBad) : False :=
  h.elim (fun hp => (f hp).inner.contradiction) (fun hq => (g hq).inner.contradiction)

theorem wrapperAntecedentFeasible (n : Nat) (_ : n = 1)
    (_ : n < 1 → NestedBad) : True := True.intro

def VerificationPassed : Prop := False → 2 + 2 = 5
def VerificationAlias : Prop := VerificationPassed
theorem verifiedClaim : VerificationAlias := fun h => h.elim

def NegationAlias : Prop := ¬ False
theorem aliasedNegation : NegationAlias := fun h => h

inductive Receipt (h : False) : Type where
  | checked

theorem certifiedClaim (h : False) (_ : Receipt h) : 2 + 2 = 5 := h.elim

inductive TrueReceipt (h : True) : Type where
  | checked

theorem feasibleDependent (h : True) (_ : TrueReceipt h) : True := h

inductive CertificateChain : Type where
  | next : CertificateChain → CertificateChain

theorem chainChecked (c : CertificateChain) : 2 + 2 = 5 := by
  induction c with
  | next _ ih => exact ih

inductive CertificateTree : Type where
  | leaf : Nat → CertificateTree
  | next : CertificateTree → CertificateTree

theorem feasibleRecursive (_ : CertificateTree) : True := True.intro

theorem ranked (rank : Nat → Nat) (step : ∀ i, rank (i + 1) < rank i) :
    2 + 2 = 5 := by
  have bound (i : Nat) : rank i + i ≤ rank 0 := by
    induction i with
    | zero => simp
    | succ i ih =>
      have h := step i
      omega
  have impossible := bound (rank 0 + 1)
  omega

theorem feasibleRanking (rank : Nat → Nat) (_ : ∀ i, rank i < rank (i + 1)) :
    True := True.intro

theorem squareChecked (n : Int) (h : n * n = -1) : 2 + 2 = 5 := by
  have nn : 0 ≤ n * n := (Int.le_total 0 n).elim
    (fun hn => Int.mul_nonneg hn hn)
    (fun hn => Int.mul_nonneg_of_nonpos_of_nonpos hn hn)
  exact ((by decide : ¬ ((0 : Int) ≤ -1)) (h ▸ nn)).elim

theorem feasibleSquare (n : Int) (_ : n * n = 4) : True := True.intro
