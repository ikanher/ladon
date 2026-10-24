namespace OriginCollision
opaque M : Nat → Nat → Nat
opaque f : Nat → Nat
opaque c : Nat
axiom same_scale_head (s x : Nat) : M s (f x) ≤ c * M (s + 1) x
end OriginCollision
