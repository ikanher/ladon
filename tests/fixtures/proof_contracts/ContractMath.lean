import Std

/-!
A bounded natural-valued scale fragment for contract feasibility.  The scale
families are uninterpreted; the theorems below establish only the stated
structural arithmetic, not analytic properties of an arbitrary norm.
-/

namespace ContractMath

/-- A proposition contract with a fixed map and explicit pre/postconditions. -/
structure Contract (X Y : Type) where
  map : X → Y
  requires : X → Prop
  guarantees : Y → Prop

def Denotes {X Y : Type} (c : Contract X Y) : Prop :=
  ∀ x, c.requires x → c.guarantees (c.map x)

/-- A is at least as permissive in its precondition and at least as strong
    in its conclusion as B.  The relation is defined by the actual predicates. -/
def Dominates {X Y : Type} (a b : Contract X Y) : Prop :=
  (∀ x, b.requires x → a.requires x) ∧
  (∀ y, a.guarantees y → b.guarantees y) ∧
  a.map = b.map

theorem dominance_sound {X Y : Type} {a b : Contract X Y}
    (hdom : Dominates a b) (ha : Denotes a) : Denotes b := by
  rcases hdom with ⟨hreq, hguar, hmap⟩
  intro x hb
  have hax := ha x (hreq x hb)
  have : a.map x = b.map x := congrFun hmap x
  rw [this] at hax
  exact hguar (b.map x) hax

/-- Explicit embeddings are required to combine two obligations at their max. -/
theorem max_requirement_and {X : Type} (Req : Nat → X → Prop)
    (GoalLeft GoalRight : X → Prop) (a b : Nat)
    (left : ∀ x, Req a x → GoalLeft x)
    (right : ∀ x, Req b x → GoalRight x)
    (embedLeft : ∀ x, Req (max a b) x → Req a x)
    (embedRight : ∀ x, Req (max a b) x → Req b x) :
    ∀ x, Req (max a b) x → GoalLeft x ∧ GoalRight x := by
  intro x h
  exact ⟨left x (embedLeft x h), right x (embedRight x h)⟩

/-- A scale-indexed estimate with an explicit natural-valued interpretation. -/
structure ScaleEstimate (X Y : Type) where
  inputScaleId : Nat
  outputScaleId : Nat
  normIn : Nat → X → Nat
  normOut : Nat → Y → Nat
  map : X → Y
  constant : Nat
  offset : Nat
  bound : ∀ s x, normOut s (map x) ≤ constant * normIn (s + offset) x

def ComposedMap {X Y Z : Type} (f : ScaleEstimate X Y)
    (g : ScaleEstimate Y Z) : X → Z := g.map ∘ f.map

def Compose {X Y Z : Type} (f : ScaleEstimate X Y)
    (g : ScaleEstimate Y Z)
    (_scaleMatch : f.outputScaleId = g.inputScaleId)
    (normMatch : ∀ s y, f.normOut s y = g.normIn s y) : ScaleEstimate X Z :=
  { inputScaleId := f.inputScaleId
    outputScaleId := g.outputScaleId
    normIn := f.normIn
    normOut := g.normOut
    map := ComposedMap f g
    constant := g.constant * f.constant
    offset := f.offset + g.offset
    bound := by
      intro s x
      have hf := f.bound (s + g.offset) x
      have hg := g.bound s (f.map x)
      calc
        g.normOut s (g.map (f.map x))
            ≤ g.constant * g.normIn (s + g.offset) (f.map x) := hg
        _ = g.constant * f.normOut (s + g.offset) (f.map x) := by
              exact congrArg (fun n => g.constant * n)
                (normMatch (s + g.offset) (f.map x)).symm
        _ ≤ g.constant * (f.constant * f.normIn ((s + g.offset) + f.offset) x) :=
              Nat.mul_le_mul_left _ hf
        _ = (g.constant * f.constant) * f.normIn (s + (f.offset + g.offset)) x := by
              simp [Nat.mul_assoc, Nat.add_comm, Nat.add_left_comm] }

theorem compose_scale_id (X Y Z : Type) (f : ScaleEstimate X Y)
    (g : ScaleEstimate Y Z) (hs : f.outputScaleId = g.inputScaleId)
    (hn : ∀ s y, f.normOut s y = g.normIn s y) :
    (Compose f g hs hn).inputScaleId = f.inputScaleId ∧
    (Compose f g hs hn).outputScaleId = g.outputScaleId := by
  exact ⟨rfl, rfl⟩

/-- For monotone input scales, a smaller loss gives a stronger estimate. -/
theorem lower_offset_implies_higher_offset {X Y : Type}
    (N : Nat → X → Nat) (M : Nat → Y → Nat) (f : X → Y)
    (monotone : ∀ i j x, i ≤ j → N i x ≤ N j x)
    {k₁ k₂ c : Nat} (hk : k₁ ≤ k₂)
    (bound₁ : ∀ s x, M s (f x) ≤ c * N (s + k₁) x) :
    ∀ s x, M s (f x) ≤ c * N (s + k₂) x := by
  intro s x
  have hindex : s + k₁ ≤ s + k₂ := Nat.add_le_add_left hk s
  exact Nat.le_trans (bound₁ s x)
    (Nat.mul_le_mul_left c (monotone (s + k₁) (s + k₂) x hindex))

/-- Valuations agree on a set of explicitly permitted binders. -/
def AgreeOn {n : Nat} (allowed : List (Fin n))
    (v w : Fin n → Nat) : Prop :=
  ∀ i, i ∈ allowed → v i = w i

def PermittedDependence {n : Nat} {Y : Type} (allowed : List (Fin n))
    (witness : (Fin n → Nat) → Y) : Prop :=
  ∀ v w, AgreeOn allowed v w → witness v = witness w

def InScope {n : Nat} (allowed visible : List (Fin n)) : Prop :=
  ∀ i, i ∈ allowed → i ∈ visible

theorem constant_witness_permitted {n : Nat} {Y : Type} (allowed : List (Fin n))
    (value : Y) : PermittedDependence allowed (fun _ => value) := by
  intro v w _
  rfl

theorem permission_monotone {n : Nat} {small large : List (Fin n)}
    (hsub : ∀ i, i ∈ small → i ∈ large) {Y : Type}
    {witness : (Fin n → Nat) → Y}
    (hperm : PermittedDependence small witness) :
    PermittedDependence large witness := by
  intro v w hagree
  apply hperm
  intro i hi
  exact hagree i (hsub i hi)

theorem permission_pair_union {n : Nat} {S T : List (Fin n)}
    {left : (Fin n → Nat) → Nat} {right : (Fin n → Nat) → Nat}
    (hleft : PermittedDependence S left)
    (hright : PermittedDependence T right) :
    PermittedDependence (S ++ T) (fun v => (left v, right v)) := by
  intro v w hagree
  apply Prod.ext
  · apply hleft
    intro i hi
    exact hagree i (List.mem_append_left T hi)
  · apply hright
    intro i hi
    exact hagree i (List.mem_append_right S hi)

/-- Combining two estimate constants preserves the union of allowed parameters. -/
theorem permission_sum_union {n : Nat} {S T : List (Fin n)}
    {left right : (Fin n → Nat) → Nat}
    (hleft : PermittedDependence S left)
    (hright : PermittedDependence T right) :
    PermittedDependence (S ++ T) (fun v => left v + right v) := by
  intro v w hagree
  have hp := permission_pair_union hleft hright v w hagree
  exact congrArg (fun p : Nat × Nat => p.1 + p.2) hp

/-- Loss maxima combine estimates only under nesting of the exact input scale.
    This theorem is distinct from the generic requirement-predicate maximum. -/
theorem combine_estimates {X Y : Type}
    (N : Nat → X → Nat) (M : Nat → Y → Nat) (f : X → Y)
    (monotone : ∀ i j x, i ≤ j → N i x ≤ N j x)
    (k₁ k₂ c₁ c₂ : Nat)
    (left : ∀ s x, M s (f x) ≤ c₁ * N (s + k₁) x)
    (right : ∀ s x, M s (f x) ≤ c₂ * N (s + k₂) x) :
    ∀ s x, M s (f x) ≤ (c₁ + c₂) * N (s + max k₁ k₂) x := by
  intro s x
  have both :
      M s (f x) ≤ c₁ * N (s + max k₁ k₂) x ∧
      M s (f x) ≤ c₂ * N (s + max k₁ k₂) x := by
    constructor
    · exact lower_offset_implies_higher_offset N M f monotone
        (Nat.le_max_left k₁ k₂) left s x
    · exact lower_offset_implies_higher_offset N M f monotone
        (Nat.le_max_right k₁ k₂) right s x
  exact Nat.le_trans both.1 (Nat.mul_le_mul_right _ (Nat.le_add_right c₁ c₂))

theorem scope_append {n : Nat} {S T visible : List (Fin n)}
    (hs : InScope S visible) (ht : InScope T visible) :
    InScope (S ++ T) visible := by
  intro i hi
  rcases List.mem_append.mp hi with h | h
  · exact hs i h
  · exact ht i h

/-- A route retains correlated loss and permitted-dependency coordinates. -/
structure Route (Binder : Type) where
  loss : Nat
  allowedDependencies : List Binder

def RouteDominates {Binder : Type} (a b : Route Binder) : Prop :=
  a.loss ≤ b.loss ∧ (∀ i, i ∈ a.allowedDependencies → i ∈ b.allowedDependencies)

def routeA : Route Nat := ⟨3, [0]⟩
def routeB : Route Nat := ⟨5, []⟩

theorem route_dominance_sound {n : Nat} {a b : Route (Fin n)}
    (hdom : RouteDominates a b)
    (N : Nat → (Fin n → Nat) → Nat) (M : Nat → Nat → Nat)
    (f : (Fin n → Nat) → Nat) (c : Nat)
    (monotone : ∀ i j v, i ≤ j → N i v ≤ N j v)
    (boundA : ∀ s v, M s (f v) ≤ c * N (s + a.loss) v)
    (witness : (Fin n → Nat) → Nat)
    (permA : PermittedDependence a.allowedDependencies witness) :
    (∀ s v, M s (f v) ≤ c * N (s + b.loss) v) ∧
      PermittedDependence b.allowedDependencies witness := by
  constructor
  · exact lower_offset_implies_higher_offset N (fun s y => M s y) f
      monotone hdom.1 boundA
  · exact permission_monotone hdom.2 permA

theorem route_tradeoff_incomparable :
    ¬ RouteDominates routeA routeB ∧ ¬ RouteDominates routeB routeA := by
  constructor
  · intro h
    have hzero := h.2 0 (by simp [routeA])
    simp [routeB] at hzero
  · intro h
    have hloss := h.1
    have impossible : ¬ (5 : Nat) ≤ 3 := by decide
    exact impossible hloss

end ContractMath

#print axioms ContractMath.dominance_sound
#print axioms ContractMath.max_requirement_and
#print axioms ContractMath.Compose
#print axioms ContractMath.lower_offset_implies_higher_offset
#print axioms ContractMath.permission_monotone
#print axioms ContractMath.permission_pair_union
#print axioms ContractMath.scope_append
#print axioms ContractMath.route_tradeoff_incomparable
#print axioms ContractMath.route_dominance_sound
#print axioms ContractMath.combine_estimates
#print axioms ContractMath.permission_sum_union

-- Reflexive transfer preserves the entire proposition, with no conversion.
#check @id
#print axioms id
