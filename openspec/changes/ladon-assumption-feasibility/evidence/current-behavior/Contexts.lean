import Lean
namespace FeasibilityProbe
-- Both conditional theorems are valid. Only the first premise context is impossible.
theorem impossible_step (n : Nat) (h0 : n = 0) (h1 : n = 1) : n = 37 := by omega
theorem impossible_use (n : Nat) (h0 : n = 0) (h1 : n = 1) : n = 37 :=
  impossible_step n h0 h1

theorem inhabited_step (n : Nat) (h0 : n = 0) : n + 1 = 1 := by omega
theorem inhabited_use (n : Nat) (h0 : n = 0) : n + 1 = 1 := inhabited_step n h0
end FeasibilityProbe
