# Design

## Context

See proposal.md. investigation_derivation.py uses rational_witness.py to check every premise and the conclusion at a supplied assignment. Quux's counterexample loop supplies a useful declared-reduction minimization pattern; its finite survival and minimality claims are deliberately scoped.

## Goals / Non-Goals

**Goals:** identify whether a countermodel challenges the original step or exposes information lost in its abstraction. **Non-Goals:** automatically repair the paper, prove universal claims by finite search, or invent function-space witnesses from unrelated scalars.

## Decisions

### Bounded loop

Consume an exact obligation and immutable source/formal contracts. Enumerate a declared finite rational/finite-domain candidate family, check all premises and the conclusion exactly, then minimize through a declared reduction relation with a strictly decreasing measure. Record every attempted candidate, rejection reason and accepted reduction. Use at most 256 candidates, 32 reductions per witness and four refinement rounds, all under the original deadline. Rational bit lengths and expression depth reuse existing checker limits.

Outcomes distinguish invalid-input, outside-assumptions, abstract-countermodel, lifted-counterexample, spurious-countermodel, survived-declared-scope, unsupported and budget-exhausted. Minimality means locally irreducible under the completely tested declared reductions; an interrupted reduction search yields a smaller witness without a minimality claim.

### Lift before claiming original falsity

A scalar assignment refuting an abstract estimate is evidence about that abstract implication. To refute an original analytic statement, require a checked construction satisfying its domain, dependence, regularity and premise constraints. If lifting is unsupported, retain an abstract discrepancy and a lifting obligation. Failure to find a lift does not itself establish that the model is spurious.

Mark spurious only with evidence that the assignment violates an original constraint or cannot realize the declared source interpretation. Such evidence may motivate an abstraction refinement. Mathematical falsity of the original prose still requires independent fidelity review.

The bounded natural-number profile has a separate source-owned public checker.
It regenerates its complete conjunction and verifies exact source bytes before
fresh supervised capture, completion, independent replay and trust checks. A
positive result is bound to the plan, original witness, interpretation, proof
term, current checker, attempt and Lean environment. No caller-provided receipt
or runner can establish a positive classification. Resource stops preserve the
original witness and lifting obligation under the original absolute deadline.

Source-defined notation or typeclass instances can change the meaning of the
generated Rat expressions, even with fully qualified type names. Therefore a
clean typed observation with opaque claim/predicate placeholders must match the
actual typed subject, captured goal and completed original goal structurally.
The placeholders never participate in checking the supplied proof. The canonical
imports must lie in the actual captured closure, and that closure's compiled
files and sidecars are reverified after the clean observation. Unavailable
canonical evidence cannot establish either positive outcome.

### Immutable refinement

A refinement adds a source-supported constraint, a checked formal implication, or a more precise representation. Record parent IDs, justification, changed features and rechecks. The original prose interpretation and original witness remain immutable. If the manuscript itself needs an extra assumption, classify that as a proposed repair in a separate branch; never count it as support for the original claim.

Recompute only affected summaries by exact dependency identities. A changed rule or context invalidates a probe or bridge when that consumer's generated proposition depends on it; display-name equality is never enough. Consumers without a checked mapping to the branch type are outside that branch's dependency graph.

### Bounded rational branch semantics

The first executable refinement semantics is deliberately limited to the closed predicate AST already checked by `rational_witness.py`. A branch checker validates its immutable branch and cited spans, copies the caller's base goal, appends every cumulative branch predicate as a premise, validates the combined goal against the existing limits, and checks one exact assignment. It binds branch, base goal, derived goal, assignment representation and checker identity in a replayable result. Canonical semantic digests use sorted compact UTF-8 JSON with `ensure_ascii=False`; assignment mapping order is irrelevant while alternate rational spellings remain distinct input identities.

This checker gives machine semantics to caller-supplied ASTs. It does not establish that a cited passage means that AST or authenticate the branch's parent lineage. Its dedicated rational ProofIR route consumes the encoded finite-assignment meaning, while generic typed source bridges and paired probes still lack an adapter from these ASTs to their source-context terms. Source formula fidelity remains unverified and the outcome applies only to the encoded derived goal.

The rational ProofIR check route creates a sibling checked-analysis artifact linking the exact plan and each generated-goal check-run. Its native batch validator rechecks those bindings against the plan, receipt and per-goal replay records. The branch record and constraints close over the derived goal, trust coverage is checked, and the original finding identity is carried through investigation finding/report/final-receipt projection. Focused mutation tests and independent review #1136 accepted this bounded finite-assignment slice. It does not authenticate process provenance or establish source fidelity, and it does not make generic bridges or paired probes depend on branches.

Task 2.2 is scoped to outputs that actually depend on the current rational refinement-branch type: the dedicated plan/check route and its checked finding/report/final-receipt projections. Exact plan regeneration and the stale-identity regression cover those dependencies. Generic source-context bridges regenerate typed obligations from an original application and native context artifacts; paired probes likewise accept typed/Nat inputs rather than this rational branch. There is no current checked mapping from rational branch predicates to terms in those contexts. Adding branch identity as metadata would not alter their generated propositions and would not be sound invalidation. A source-to-formal realization or typed constraint-binding operation is a separate prerequisite before those unrelated routes can claim branch dependence.

### Public workflow and historical report supplements

The public `investigation contract refine` command checks one supplied rational
witness, runs the fresh source-owned Nat/rational lift owner, then checks
source-cited and proposed-repair constraints in separate sibling branches. This
single-witness workflow uses one absolute deadline; it does not launch another
candidate search or automatically retry after a resource stop. It preserves
the request, original rational check, saved lift result and every completed
branch in an immutable versioned artifact.

`contract inspect` recomputes the rational evidence and verifies current source
hashes/citations, but gives saved Lean claims only historical, unverified
authority. Hashes bind contents, not external process provenance. A fresh lift
requires an explicit new `refine` invocation. `investigation report --refinement`
accepts up to four such supplements, requiring each original finding ID to
match an existing report finding. This association is explicitly attributed by
ID; it does not certify that the rational encoding translates that finding.
Report v3 keeps the original observation and branch findings, adds refinement
references and historical evidence, and leaves pending review work intact.
Supplements do not mutate plans or enter finalization receipts. The earlier
native rational branch attachment route remains the final-receipt consumer.

See the [public CLI example](../../../docs/CONTRACT_REFINEMENT.md). Source-cited
constraints retain their formula-fidelity obligation, even when a fresh Lean
proof establishes incompatibility for the selected formal interpretation.

## Risks / Trade-offs

The bounded lifting precursor now generates full-claim and per-object
equivalences for an explicit natural-number interpretation, then a realization
or range-incompatibility goal for the exact rational witness. Its
[constructed native experiment](evidence/native-lift-feasibility.md) passed
six cases, including omitted-assumption and admitted-proof controls, under
independent review #1240. Planning keeps source verification and positive lift
authority false. The [accepted public owner](evidence/public-lift-check.md) now regenerates the
plan from fresh source and environment identities, checks the complete
conjunction and canonical semantics, and binds native evidence before exposing a
positive result. This bounded route does not make generic typed source bridges
consume rational branches or establish prose fidelity.

- Refinement can always explain away a real bug → require source or checked evidence for every added constraint and keep repair branches separate.
- Abstract witnesses cannot be lifted → report the unresolved lifting goal; do not force analytic claims into the rational fragment.
- Reduction falsely claims global minimality → expose relation, candidate scope and completed reduction coverage.
- Loop consumes the audit → a 30-minute feasibility set must include one real witness, one proved-spurious witness and one unsupported lift under the parent caps; stop widening if these cannot be distinguished.

## Migration Plan

Use domain analysis revision links and existing immutable observation histories. Add no implicit mutation to plan inputs or previous findings. A retry after a resource stop requires a new explicit attempt under the existing stop-and-report policy.

