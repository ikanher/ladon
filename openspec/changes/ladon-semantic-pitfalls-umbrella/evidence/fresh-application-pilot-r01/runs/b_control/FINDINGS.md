# Control audit findings

## Verdict

**Supported.** `Nat.sInf_mem` directly proves the stated membership once nonemptiness of the set is supplied. The set `{n : ℕ | a ≤ n}` is nonempty because it contains `a`.

## Exact formal claim and assumptions

The candidate formalizes the claim as

```lean
def Claimed (a : ℕ) : Prop := sInf {n : ℕ | a ≤ n} ∈ {n : ℕ | a ≤ n}
```

There is no additional hypothesis on `a`; it is an arbitrary natural number. The invoked theorem has type

```lean
Nat.sInf_mem {s : Set ℕ} (h : s.Nonempty) : sInf s ∈ s
```

Thus its sole explicit premise is that the set is nonempty. For this set, the witness is `a`, with `a ≤ a` proved by reflexivity (Lean closes the set-membership goal by `simp`).

## Evidence

- `lake env lean Owner.lean` printed the theorem type above.
- Inspected the pinned source at `.lake/packages/mathlib/Mathlib/Order/Lattice/Nat.lean:80-84`: the theorem assumes `s.Nonempty`, then rewrites the natural infimum using `Nat.sInf_def` and applies `Nat.find_spec`.
- Created `runs/b_control/Check.lean` (scratch only) with the same definition and this complete proof:

  ```lean
  example (a : ℕ) : Claimed a := by
    unfold Claimed
    exact Nat.sInf_mem ⟨a, by simp⟩
  ```

  `lake env lean ../../runs/b_control/Check.lean` completed successfully with no errors.
- The provided `Query.lean` ends with `skip`; `lake env lean Query.lean` consequently reported the remaining goal `Claimed a`. That file does not itself supply a proof; the complete scratch application above does.

## Limitations

This verifies the formal candidate in the assigned pinned project and matches the passage's natural-number interpretation. It does not establish any broader claim about infima in other orders or about an unstated set representation.
