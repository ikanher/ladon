import Lean
namespace Contexts
theorem both (n m : Nat) (hn : 0 < n) (hm : 0 < m) : 0 < n ∧ 0 < m := And.intro hn hm
theorem bounded (n : Nat) (h : n < 5) : n < 5 := h
theorem dependent (n : Nat) (i : Fin n) : True ∧ True := And.intro True.intro True.intro
theorem ordered (n m : Nat) (hn : 0 < n) (hm : 0 < m) : 0 < n ∧ 0 < m := both n m hn hm
theorem represented (n : Nat) (h : n < 5) : n < 5 := bounded n h
end Contexts
