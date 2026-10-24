/-! Adversarial local-instance declarations: same surface shape, altered semantics. -/
namespace ProducerAdversarial

opaque M : Nat → Nat → Nat
opaque N : Nat → Nat → Nat
opaque f : Nat → Nat
opaque c : Nat

section
  local instance : HMul Nat Nat Nat where
    hMul := fun _ _ => 0

  axiom custom_mul (s x : Nat) : M s (f x) ≤ c * N (s + 0) x
end

section
  local instance : HAdd Nat Nat Nat where
    hAdd := fun _ _ => 0

  axiom custom_add (s x : Nat) : M s (f x) ≤ c * N (s + 0) x
end

section
  local instance : LE Nat where
    le := fun _ _ => True

  axiom custom_le (s x : Nat) : M s (f x) ≤ c * N (s + 0) x
end

section
  local instance : OfNat Nat 2 where
    ofNat := 999

  axiom custom_offset (s x : Nat) : M s (f x) ≤ c * N (s + 2) x
end

end ProducerAdversarial

namespace Different
  axiom qualified_name_need_not_match_module (s x : Nat) :
    ProducerAdversarial.M s (ProducerAdversarial.f x) ≤
      ProducerAdversarial.c * ProducerAdversarial.N (s + 1) x
end Different
