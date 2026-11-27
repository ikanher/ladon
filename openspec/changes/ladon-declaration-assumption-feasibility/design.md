# Design

## Context

The [native probe](../ladon-assumption-feasibility/evidence/native-probe/README.md) builds a feasibility proposition from `ConstantInfo.type`. It generated the joint arithmetic premise for `silly_theorem`. For `prove_anything`, Lean inferred `BadStructure : Prop`, and Ladon's proof slice found `BadStructure.contradiction h : False`. The candidate checker accepted the projection as a proof of `¬ BadStructure`. The probe rejected `P : Prop` as an unsupported parameter. The first implementation added exact declaration selection, automatic refutation and independent replay. The [review cases](specs/ladon-declaration-assumption-feasibility/spec.md#scenario-elementary-propositional-contradictions) extend the range of declarations that must receive a checked finding.

### Acceptance fixtures (Lean 4.32.1)

```lean
theorem silly_theorem (n : Nat)
    (h1 : n = 0) (h2 : n = 1) : 2 + 2 = 5 := by
  have h : (0 : Nat) = 1 := h1.symm.trans h2
  have impossible : False := Nat.zero_ne_one h
  exact False.elim impossible

structure BadStructure where
  contradiction : False

theorem prove_anything (P : Prop) (h : BadStructure) : P := by
  exact False.elim h.contradiction

#print axioms prove_anything
```

## Goals / Non-Goals

**Goals**

- Offer one bounded, opt-in theorem check against an existing compiled module.
- Reuse the native closure rules, compiled input inventory, replay resource controls, and standard axiom policy.

**Non-Goals**

- Proof-position analysis, fixed assignments, positive witness search, whole-project lint, and prose judgment belong outside this increment. The [broader feasibility packet](../ladon-assumption-feasibility/proposal.md) retains its own acceptance criteria.

## Decisions

1. Add `ladon theorem feasibility NAME --repo-root REPO --module MODULE` with the existing pinned Lean and Lake executable options, text and JSON output, and finite resource limits. An explicit module supports exact root-level names and keeps the check usable without an index. Reuse the compiled-environment loader and ownership check. Keep the result bound to the observed compiled module and dependencies. Live source freshness may be reported only when independently verified.
2. Read the consecutive outer `Π` binders of the compiled declaration type after bounded reduction of transparent aliases at the head. This treats an explicit top-level implication as a premise, even if it was written to the right of the declaration's colon. The remaining proposition is the conclusion. Conjoin proof hypotheses whose types can be represented faithfully. For each non-proof binder, construct an existential over its actual Lean domain using the domain's inferred universe level. Preserve dependencies on earlier data parameters, including type parameters. This also admits values of structures in `Type`. Quantify an earlier proof term existentially when another binder depends on it, and pass that witness back to search as a proof. A proof whose witness is independent of the remaining binder types contributes a conjunct. For example, `P : Prop` introduces an existential parameter and `h : P` contributes the proposition `P`. Keep the existential for `P` even when no hypothesis refers to it. Preserve binder order and dependencies, and reject unsupported telescope shapes. Build the proposition as a Lean expression and carry its identity through replay.
   Use a bounded traversal of the `Expr.forallE` nodes exposed from `ConstantInfo.type`. At each binder boundary, reduce at most 64 transparent headline aliases and lets, preserving `Not` as the conclusion head. Lean 4.32.1's `forallBoundedTelescope` unfolds definitions while looking for more binders. In the native probe it returned the premise `False` for both `¬ False` and `False → False`. The remaining conclusion can be checked for propositionality after fixing the boundary. Zero proof hypotheses contribute `True`, one contributes its type directly, and multiple hypotheses form an ordered conjunction. If traversal hits its bound before the boundary, report incomplete coverage.
3. Unpack the joint premise inside the refutation. Retain both existential witnesses and proof hypotheses so a structure value in either group can supply fields. Use Lean's structure metadata to project well-typed fields recursively. Keep each projected expression tied to its parent witness so comparisons such as `n < 2` and `n > 5` refer to the same `n`.
   Search the accumulated proof facts for `False` and complementary propositions. Apply available nondependent implications to matching proofs, including negations as implications to `False`. Deduplicate derived facts and keep their proof terms. Give original and projected linear `Nat` and `Int` constraints to `omega`. Use finite projection depth, fact and inference budgets with defaults sufficient for the acceptance cases. If a budget cuts the search short, retain any independently verified refutation already found or report the exhausted bound. Project fields of newly derived proofs under the same resource limits and feed the projected propositions back into implication search. If the earlier search completes within its limits, try bounded `grind only` using the local hypotheses, witnesses, and derived proof facts. For an implication with a structure result, project from its application to a temporary antecedent proof, then abstract that proof to obtain conditional field facts. Count those projections toward the shared search limits. The fallback can then establish an antecedent through arithmetic or by splitting cases and use the corresponding fields. Equality reasoning can also combine positive and negative facts. Use four case splits per branch and four E-matching rounds before each split, under the existing worker resource limits. For a natural-number sequence with a verified step hypothesis `∀ i, rank (i + 1) < rank i`, instantiate an induction proof of impossibility. For visible integer self-products, derive nonnegativity from `Int.sq_nonneg` and add it to the arithmetic context under the fact budget. Try kernel induction on eligible single recursive inductive families and accept that route when every constructor branch can close with its local hypotheses. A completed search without a replayed refutation is inconclusive.
4. Transfer the closed proof and its reachable generated auxiliaries as native Lean declarations in a private temporary artifact. Replay in a fresh Lean process with synchronous kernel checking. Reconstruct the exact premise expression from the owning compiled theorem, verify the certificate's subject against that expression, and add the refutation at its negation. The native transfer preserves the proof expression and its auxiliaries across the process boundary.
   Choose the certificate's Lean name against the loaded environment and the names of the generated auxiliaries. Carry that exact name through serialization, replay and the dependency audit. Replay checks freshness before insertion and starts its audit from the declaration it just kernel-checked.
   Check independence and axiom trust through a bounded walk of the certificate's transitive constant dependencies, including declaration types, values, and generated auxiliaries. Reject a path to the reviewed theorem. Missing dependency coverage or an exhausted bound withholds acceptance. Importing the owner module permits access to its types and projections.
5. Return human-readable and structured output with status, reason, exact declaration and environment, premise proposition, operation bounds, and replay and trust status. Report `inconsistent` only for an accepted replay. Use `unresolved` for unsupported or inconclusive checks and retain the CLI's existing operational-error conventions for failures. Use the established CLI exit classes. A completed mathematical assessment (`inconsistent` or inconclusive/unsupported `unresolved`) exits 0 and callers read the status. Execution failures and resource stops exit 1 with a reason and no accepted finding. With `--fail-on-unresolved`, every `unresolved` result exits 1 and retains its structured verdict. Invalid selection exits 2. The reported input is the compiled module, including when its source has subsequently changed.

## Risks / Trade-offs

- The prototype's `omega` result previously failed replay on a generated auxiliary. Native transfer carries the auxiliary declarations in dependency order so the replay process can check each one before checking the refutation. The direct `omega` call produced a closed proof on the arithmetic fixture. An additional certificate fixture exercises native transfer with a generated auxiliary.
- A field name or the presence of `False.elim` in a proof body gives no feasibility evidence. Exercise the projection route with a renamed field and a theorem that has the same impossible premises with a trivial proof. Exercise a structure with an inhabited field and a genuine temporary contradiction inside its proof as a control.
- Compiled inputs may change during the check. Match the import closure across processes and verify file identities and contents across the check. Pretty-printing serves the display, and the kernel checks the native expression.
- A failed tactic is inconclusive. An inhabited control and a correct proof with an internal contradiction branch both exercise this rule. Keep the announcement advisory even when declared hypotheses are inconsistent.
