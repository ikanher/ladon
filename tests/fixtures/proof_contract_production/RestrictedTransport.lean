/-
Standalone Core Lean fixture. The guarded view and subtype-restricted view are
equivalent; removing the membership predicate is not.
-/

def Restricted (P Q : Nat → Prop) : Prop :=
  ∀ x : {n : Nat // P n}, Q x.val

def Guarded (P Q : Nat → Prop) : Prop :=
  ∀ n : Nat, P n → Q n

theorem subtype_to_guarded (P Q : Nat → Prop) :
    Restricted P Q ↔ Guarded P Q := by
  constructor
  · intro h n hn
    exact h ⟨n, hn⟩
  · intro h x
    exact h x.val x.property

theorem alpha_renamed_presentation (P Q : Nat → Prop) :
    (∀ y : {k : Nat // P k}, Q y.val) ↔ (∀ z : Nat, P z → Q z) := by
  constructor
  · intro h z hz
    exact h ⟨z, hz⟩
  · intro h y
    exact h y.val y.property

def RestrictedExample : Prop :=
  Restricted (fun n : Nat => n = 0) (fun n : Nat => n = 0)

def ErasedExample : Prop :=
  ∀ n : Nat, n = 0

theorem membership_erasure_is_not_equivalent :
    ¬ (RestrictedExample ↔ ErasedExample) := by
  intro equivalence
  have restricted : RestrictedExample := by
    intro x
    exact x.property
  have erased : ErasedExample := equivalence.mp restricted
  have impossible : Nat.succ 0 = 0 := erased 1
  exact Nat.noConfusion impossible

#print axioms subtype_to_guarded
#print axioms alpha_renamed_presentation
#print axioms membership_erasure_is_not_equivalent
