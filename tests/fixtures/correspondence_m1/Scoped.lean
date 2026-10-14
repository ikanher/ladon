import Lean

namespace Scoped

theorem bridge (n : Nat) (h : 0 < n) : 0 < n := h
theorem combine (n m : Nat) (hn : 0 < n) (hm : 0 < m) : 0 < n ∧ 0 < m :=
  And.intro hn hm

theorem witness (h : ∃ k : Nat, 0 < k) : ∃ k : Nat, 0 < k :=
  Exists.elim h (fun k hk => Exists.intro k (bridge k hk))

theorem branches (n m : Nat) (h : 0 < n ∨ 0 < m) : 0 < n ∨ 0 < m :=
  Or.elim h
    (fun hn => Or.inl (bridge n hn))
    (fun hm => Or.inr (bridge m hm))

theorem chain (n m : Nat) (hn : 0 < n) (hm : 0 < m) : 0 < n ∧ 0 < m := by
  have first : 0 < n := bridge n hn
  have second : 0 < m := bridge m hm
  exact combine n m first second

end Scoped
