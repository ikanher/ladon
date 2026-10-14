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

## Follow a new discrepancy and a faithful control

Read [case e03](../openspec/changes/ladon-correspondence-discovery-umbrella/evidence/implementation/evaluation/cases/e03/INPUT.md) and its retained [assisted first report](../openspec/changes/ladon-correspondence-discovery-umbrella/evidence/implementation/evaluation/runs/e03-ladon-assisted/first-report.json). The exposition asks for one real y with x+y=0 for every real x; the supplied formal proposition chooses a y for each x. Preserve the original quantifier order. Taking x=0 forces the common y to be zero; taking x=1 then gives a contradiction. This is a conventional counterargument and a localized statement mismatch, not a report of a failed tactic.

Now read [case e09](../openspec/changes/ladon-correspondence-discovery-umbrella/evidence/implementation/evaluation/cases/e09/INPUT.md) and its [assisted first report](../openspec/changes/ladon-correspondence-discovery-umbrella/evidence/implementation/evaluation/runs/e09-ladon-assisted/first-report.json). Both texts allow y to depend on x and choose y=-x. The assertion and witness agree. A comparison procedure must accept this control rather than flagging the presence of an existential quantifier alone.

These files and the displayed arguments are sufficient to follow the reviews without a model service or a Quux checkout. They are elementary synthetic examples; actual formal source, argument inspection and source coverage remain necessary for a research exposition. The [pilot report](../openspec/changes/ladon-correspondence-discovery-umbrella/evidence/implementation/evaluation/REPORT.md) preserves the underspecified control, additional omissions, incidental report errors, resource measurements and attribution limits.
