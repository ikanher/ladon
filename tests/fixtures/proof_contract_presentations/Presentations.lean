namespace Presentations
opaque M : Nat → Nat → Nat
opaque N : Nat → Nat → Nat
opaque f : Nat → Nat
opaque c : Nat
axiom implicit_index {s : Nat} (x : Nat) : M s (f x) ≤ c * N (s + 3) x
axiom explicit_index (s x : Nat) : M s (f x) ≤ c * N (s + 3) x
axiom nested_witnesses : ∃ d c : Nat, ∀ s x : Nat, M s (f x) ≤ c * N (s + d) x
axiom unknown_shift (s x : Nat) : M s (f x) ≤ c * N (s * 2) x
end Presentations
