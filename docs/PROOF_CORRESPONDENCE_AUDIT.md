# Audit a proof passage, not just its conclusion

A Lean proof of the final theorem can coexist with a false intermediate argument, a missing informal existence assumption, or a valid alternative proof. Ladon's correspondence workflow keeps those questions separate. Ordinary Markdown/TeX, named Lean obligations, and compiler/axiom output are sufficient; a Ladon command or model account is not required.

Start from an unchanged source passage and its proposed formal counterpart. State the exact local assertion in its original context, inspect or check that assertion, and propose a small revision. Keep a failed attempt separate from a checked counterexample. Label added assumptions as narrowing, and read proof source before claiming that a particular argument was translated.

For an investigation without a supplied fault location, use the
[source-first discovery procedure](CORRESPONDENCE_DISCOVERY.md). It adds a
breadth pass, source-span inventory, explicit unexamined population and
consumer-directed comparison before concentrating on a proof slice. Its
[development evidence](../openspec/changes/ladon-correspondence-discovery-umbrella/evidence/implementation/README.md)
records known-case exercises and controls separately from withheld evaluation.
The [frozen two-arm pilot](../openspec/changes/ladon-correspondence-discovery-umbrella/evidence/implementation/evaluation/REPORT.md) exercised 28 fresh attempts on fourteen elementary authored inputs. Both arms found the same discrepancies with no false alarms; assistance used more observed time and tokens. No detection advantage or research-paper effectiveness was demonstrated. The supplied formal counterparts were summaries, and no scored run performed Lean checking.

The [r70 exercised recipe](../openspec/changes/ladon-proof-correspondence-audit-umbrella/evidence/r70/AUDIT_RECIPE.md) provides concrete commands and evidence:

| Boundary | Development case |
|---|---|
| Wrong step, true final theorem | A polynomial's false factorization is refuted at zero; a different correct factorization proves the original inequality. |
| Total default, missing existence | An empty natural-number set has a formal `sInf` default; later algebra does not establish membership or existence. |
| Valid proof, different method | Direct symmetry and spectral diagonalization both prove nonnegative trace, but their proof strategies differ. |
| Changed estimate, open implication | A pinned inverse-estimate declaration requests five additional derivatives while the cited paper asserts four. The stronger guarantee remains an unresolved formal connection, not a refuted theorem. |

The [findings and proposed corrections](../openspec/changes/ladon-proof-correspondence-audit-umbrella/evidence/r70/README.md) retain original sources, new checks, failed attempts, authorship and adoption status. These are known published examples with authored controls, not a blind fidelity-detection benchmark. No general reader-benefit claim follows.

Use existing [assessment and exposition mechanisms](RESULT_EXPOSITION.md) when a revision-bound companion helps a real reader. They display attributed reviews; they do not automatically discover semantic discrepancies. [Source-goal completion](SOURCE_GOAL_COMPLETION.md) remains optional when an application must be tied to its captured original goal. It does not by itself verify the meaning or strategy of an informal argument.

The governing motivation remains [precise exposition and honest informal/formal correlation](../openspec/changes/ladon-result-understanding-and-release-umbrella/sources.md), supporting mathematics that readers can understand, question and reuse. The r70 investigation closes with the existing tools and its explicit unresolved scope. Further interface expansion needs an actual missing operation or failure; another known example is not automatically the next milestone.

## Check a formula against its definitions

When a passage reconstructs an object, changes coordinates, or converts between
representations, compare the claimed formula with the defining identity before
searching for a theorem. This is a source-review recipe using existing tools;
Ladon does not automatically select or interpret the formulas.

1. Give each assertion a stable ID, source span, original domain and quantifiers.
   List nearby defining equalities, side conditions and conventions. Include
   intermediate assertions even when the final theorem compiles.
2. Substitute the claimed reconstruction back into its definition. Check inverse
   factors, signs, inequality direction, units and endpoint domains. A mismatch
   is a candidate obligation; it is not yet a premise-satisfying counterexample.
3. Freeze the original implication and a separate candidate repair. Find an
   assignment satisfying every original premise. If the quantities are laws,
   functions or integrals, justify that the assignment can actually arise in
   that source setting. An inconsistent ambient context cannot refute a claim.
4. Use the [local derivation workflow](DERIVATION_CHALLENGES.md) when the exact
   implication fits its rational fragment: `init --derivations`, author the
   contract/arithmetic, then `investigation witness`. Keep the plan, assignment,
   exact evaluated premises/conclusion and command output. Use ordinary Lean or
   reviewed mathematics for unsupported operations. Replacing exp(t) by a scalar
   parameter is an authored abstraction whose source correspondence needs proof.
5. Check a repaired formula and a degenerate/boundary control. `not-counterexample`
   describes one assignment; universal support needs its own argument.
   `outside-assumptions` rejects a witness, not the original implication.
6. Before treating a formal declaration as support, write the explicit object
   map in both directions: signs, pushforwards, laws, normalization and parameter
   domains. Similar names or a successful `#check` do not establish that map.
   A useful restricted theorem keeps its own support ID instead of replacing
   the original source claim or control.
7. Freeze the complete evidence before review. Reviewers must return the same
   IDs and source labels; reject omissions and ID mismatches before acceptance.
   Record whether reviewers received hints or known answers. Preserve first
   reports and put corrections and additional coverage in separate records.

The [PLD audit](../openspec/changes/ladon-pld-core-source-audit/evidence/pld-core-r03/REPORT-v2.md)
found a real inverse-factor error by this reasoning and identified a nontrivial
sign map between paper and formal loss laws. The
[exposed scalar qualification](../openspec/changes/ladon-semantic-pitfalls-umbrella/evidence/source-consistency-r01/REGISTRATION.md)
checks the existing witness operation with a fault, repair, degenerate control
and invalid assignment. These are development evidence, not a discovery score.

## Follow a new discrepancy and a faithful control

Read [case e03](../openspec/changes/ladon-correspondence-discovery-umbrella/evidence/implementation/evaluation/cases/e03/INPUT.md) and its retained [assisted first report](../openspec/changes/ladon-correspondence-discovery-umbrella/evidence/implementation/evaluation/runs/e03-ladon-assisted/first-report.json). The exposition asks for one real y with x+y=0 for every real x; the supplied formal proposition chooses a y for each x. Preserve the original quantifier order. Taking x=0 forces the common y to be zero; taking x=1 then gives a contradiction. This is a conventional counterargument and a localized statement mismatch, not a report of a failed tactic.

Now read [case e09](../openspec/changes/ladon-correspondence-discovery-umbrella/evidence/implementation/evaluation/cases/e09/INPUT.md) and its [assisted first report](../openspec/changes/ladon-correspondence-discovery-umbrella/evidence/implementation/evaluation/runs/e09-ladon-assisted/first-report.json). Both texts allow y to depend on x and choose y=-x. The assertion and witness agree. A comparison procedure must accept this control rather than flagging the presence of an existential quantifier alone.

These files and the displayed arguments are sufficient to follow the reviews without a model service or a Quux checkout. They are elementary synthetic examples; actual formal source, argument inspection and source coverage remain necessary for a research exposition. The [pilot report](../openspec/changes/ladon-correspondence-discovery-umbrella/evidence/implementation/evaluation/REPORT.md) preserves the underspecified control, additional omissions, incidental report errors, resource measurements and attribution limits.

## Trace a conclusion back to its premise

A selected application can show that a proof uses a conclusion-bearing local or instance. Follow the actual application arguments into the same scoped local context, then follow local `let` values to their providers. Match structural local IDs; display names only help navigation. A type-class projection can be a legitimate conditional interface, a hidden premise, or a field backed by an independently proved value. Inspect the provider's source before judging which one.

Keep three questions separate: what the original proof uses, whether Lean checks the selected projection/type, and whether the prose discloses or establishes that premise. A route alone proves neither necessity nor circularity. Compare the exact passage and declared scope with the complete formal telescope. Preserve unresolved providers and unexamined source spans. A successful selected slice does not certify the whole theorem.

The [premise comparison recipe](../openspec/changes/ladon-premise-provenance/evidence/premise-comparison-r01/RECIPE.md) gives a step-by-step procedure and the [reviewed result](../openspec/changes/ladon-premise-provenance/evidence/premise-comparison-m2-r01/ADJUDICATION.md) shows a conclusion-bearing assumption, a disclosed conditional, an independently derived provider, and a real Gaussian moment route. Those are exposed development examples. They do not show autonomous prose discovery or a detection advantage. Use this recipe to gather and explain scoped evidence; obtain source review before calling an omitted premise an exposition error.


## Check a complete application under the source assumptions

First record the passage's objects, assumptions, quantifiers, conclusion and ambiguous readings before looking at a proposed owner theorem. Keep later interpretation changes explicit. For known development examples disclose prior exposure; this first-pass procedure does not erase it.

Encode the attributed source context and conclusion in a local Lean goal. Apply the selected theorem at one consistent object/parameter assignment and include the conclusion transfer in the proposed full term. Account for theorem arguments with cited source assumptions, checked derivations or unresolved obligations. Equivalent wording and stronger assumptions can supply a premise; a complete table alone cannot establish support. Preserve dependent locals, lets and fixed assignments. Check the whole route with [source-goal capture](SOURCE_GOAL_CAPTURE.md) followed by [completion](SOURCE_GOAL_COMPLETION.md), using the actual context rather than checking the theorem against its own printed type.

Inspect the structured outcome, replay and trust. An unresolved premise or conclusion transfer blocks completed support for that route; it does not establish necessity or source falsity. A transformed object or another proof may support the original claim. Preserve repairs as separate claims. To refute the source, independently check a counterexample satisfying every original premise in the original mathematical setting.

For diagnosis, an expression-form partial application can retain a missing argument as an explicit residual. A tactic `?_` can instead be admitted as `sorryAx`: the final trust rejection blocks completion even when its residual list is empty. An empty residual list or exit zero alone is never acceptance. If valid ordinary Lean code fails the completion helper's closure/round-trip step, retain the exact failure and the separate ordinary compiler/axiom evidence; do not label that a native completion success or infer that the source claim is false.

Keep pristine capsule payloads separate from working projects with packages/build outputs. Source capture/completion does not require capsule replay when the necessary compiled imports are already available; record cache provenance and actual toolchain bindings. Keep measurable-limit claims separate from samplewise existence, and check library definitions such as real `Summable` instead of importing the familiar meaning of ordered conditional convergence.

The [C05 printer repair](../openspec/changes/ladon-semantic-pitfalls-umbrella/evidence/c05-printer-fix-r01/REPORT.md) now lets the previously rejected shifted-state proof complete through the native capture, replay and trust path. Proof printing uses a finite step budget and reports omitted terms directly. A longer future proof can still exceed the bound; preserve that rejection and use the separate ordinary Lean route when necessary. The original N.3c report remains the pre-fix result.

The [exposed seven-case qualification](../openspec/changes/ladon-semantic-pitfalls-umbrella/evidence/checked-application-n3c-r01/REPORT.md) retains faithful, omitted/derived/conditional, shifted-object, shared-parameter and quantifier cases. It exercises existing checks and ordinary Lean with supplied interpretations and proofs. It is not a fresh discovery comparison or evidence of incremental detection benefit.
