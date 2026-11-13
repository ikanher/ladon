# Control audit findings

## Verdict

The unconditional source claim is false as written. `Nat.sInf_mem` supports membership only when the set is nonempty. Under the pinned Mathlib convention, `sInf ∅ = 0`, and `0 ∉ ∅`, so the empty set is a concrete counterexample.

## Exact assumptions

The candidate declaration has the exact type:

```lean
Nat.sInf_mem {s : Set ℕ} (h : s.Nonempty) : sInf s ∈ s
```

Thus its result requires a proof of `s.Nonempty`. It proves the passage's claim for nonempty `S`; the passage supplies no such hypothesis.

## Evidence and commands

- Read `unit_a/passage.md` before reading source and recorded its unconditional universal interpretation in `runs/a_control/FIRST.md`.
- Inspected `unit_a/project/Owner.lean` and `Query.lean`: `Claimed S` is exactly `sInf S ∈ S`, and the query's example has no nonemptiness assumption.
- In pinned local Mathlib `Mathlib/Order/Lattice/Nat.lean`, lines 80–82 define `sInf_mem` with `h : s.Nonempty`. The same file gives `sInf_empty : sInf ∅ = 0` at lines 68–71.
- Ran from `unit_a/project`:

  ```sh
  lake env lean ../../runs/a_control/Check.lean
  ```

  Output confirmed `Nat.sInf_mem {s : Set ℕ} (h : s.Nonempty) : sInf s ∈ s`. The scratch file also compiled a direct application under `h : S.Nonempty`, the counterexample `¬ (sInf (∅ : Set ℕ) ∈ ∅)` by `simp`, and `sInf (∅ : Set ℕ) = 0` by `simp`.

## Limitations

This audit addresses only the stated claim, its candidate theorem, and the local pinned Mathlib source for unit A. It does not establish anything about other units or broader custody/provenance context.
