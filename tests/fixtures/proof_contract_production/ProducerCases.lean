/-! Small source declarations for the producer feasibility gate.

These are deliberately axioms: extraction must inspect elaborated statement
types and must not depend on a proof body or a pretty-printed signature.
-/

namespace ProducerCases

opaque M : Nat → Nat → Nat
opaque N : Nat → Nat → Nat
opaque f : Nat → Nat
opaque c : Nat

-- Supported core shape: forall scale and input, indexed estimate.
axiom supported_base (s x : Nat) : M s (f x) ≤ c * N (s + 0) x

-- Alpha-renamed presentation of the same telescope and estimate.
axiom supported_alpha (scale input : Nat) :
  M scale (f input) ≤ c * N (scale + 0) input

-- A local definition aliases the shifted output scale.
axiom supported_let_alias (s x : Nat) :
  let shifted := s + 2
  M s (f x) ≤ c * N shifted x

-- The existential estimate constant is chosen after s and may depend on it.
axiom supported_witness_after_scale (s : Nat) :
  ∃ c : Nat, ∀ x : Nat, M s (f x) ≤ c * N (s + 0) x

-- Here the existential constant is chosen before s and is independent of s.
axiom supported_witness_before_scale :
  ∃ c : Nat, ∀ s x : Nat, M s (f x) ≤ c * N (s + 0) x

-- A second shifted estimate keeps the explicit offset and telescope visible.
axiom supported_scale_input (s x : Nat) :
  M s (f x) ≤ c * N (s + 3) x

-- Unsupported dependent domain: the input type varies with s.
axiom unsupported_dependent_domain (s : Nat) (x : Fin (s + 1)) :
  M s (f x.val) ≤ c * N s x.val

-- Unsupported restricted input set. Replacing this subtype by Nat erases the
-- membership evidence carried by the value; keep it unsupported or residual.
axiom unsupported_membership (s : Nat) (x : {n : Nat // s < n}) :
  M s (f x.val) ≤ c * N s x.val

end ProducerCases
